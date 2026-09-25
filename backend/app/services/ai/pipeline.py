"""
AIProcessingPipeline: orchestrates the full voice -> structured, reviewable
patient summary flow.

    Audio -> STT -> Transcript -> LLM structured extraction -> Pydantic
    validation (retry on failure) -> Hybrid risk detection -> Persisted
    PatientSummary + RiskFlag rows in PENDING_REVIEW state.

This is intentionally synchronous per-request for the academic v1 scope
(see docs/architecture.md for why): the frontend polls GET /api/jobs/:id
for progress, and the ProcessingJob row records each stage so the flow
looks and behaves like a real async pipeline even though it currently runs
inline. Swapping in a Celery/RQ worker later only requires changing how
`run()` is invoked, not its internals.
"""
import json
import time
import uuid
import logging

from pydantic import ValidationError

from app.extensions import db
from app.models.handoff import (
    HandoffRecording, ProcessingJob,
    JOB_TRANSCRIBING, JOB_ANALYSING, JOB_RISK_DETECTION, JOB_COMPLETED, JOB_FAILED,
)
from app.models.summary import PatientSummary, RiskFlag, AIProcessingLog, REVIEW_PENDING
from app.schemas.ai_schema import HandoffExtractionResult
from app.services.ai.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt, PROMPT_VERSION
from app.services.risk.detection_service import RiskDetectionService

logger = logging.getLogger("handovermind.ai_pipeline")


class AIProcessingError(Exception):
    pass


class AIProcessingPipeline:
    def __init__(self, stt_provider, llm_provider, max_retries: int = 2):
        self.stt_provider = stt_provider
        self.llm_provider = llm_provider
        self.max_retries = max_retries
        self.risk_service = RiskDetectionService()

    def _log(self, recording_id, request_id, stage, provider, model, status,
              duration_ms, token_usage=None, retry_count=0, validation_result=None):
        db.session.add(AIProcessingLog(
            recording_id=recording_id, request_id=request_id, stage=stage,
            provider=provider, model=model, status=status, duration_ms=duration_ms,
            token_usage=token_usage, retry_count=retry_count, validation_result=validation_result,
        ))

    def run(self, recording: HandoffRecording, audio_path: str, content_type: str) -> ProcessingJob:
        job = recording.processing_job or ProcessingJob(recording_id=recording.id)
        request_id = str(uuid.uuid4())
        job.stt_provider = self.stt_provider.name

        try:
            # --- Stage 1: Transcription ---
            job.status = JOB_TRANSCRIBING
            recording.status = JOB_TRANSCRIBING
            db.session.add(job)
            db.session.commit()

            t0 = time.time()
            stt_result = self.stt_provider.transcribe(audio_path, content_type)
            self._log(recording.id, request_id, "STT", self.stt_provider.name, None,
                       "SUCCESS", stt_result.duration_ms)

            recording.transcript = stt_result.transcript
            recording.transcript_provider = stt_result.provider
            db.session.commit()

            # --- Stage 2: LLM structured extraction (with validation retries) ---
            job.status = JOB_ANALYSING
            recording.status = JOB_ANALYSING
            job.llm_provider = self.llm_provider.name
            job.prompt_version = PROMPT_VERSION
            db.session.commit()

            extraction = self._extract_with_retries(recording, request_id)

            # --- Stage 3: Hybrid risk detection ---
            job.status = JOB_RISK_DETECTION
            recording.status = JOB_RISK_DETECTION
            db.session.commit()

            self._persist_summaries(recording, extraction, stt_result.transcript)

            job.status = JOB_COMPLETED
            recording.status = JOB_COMPLETED
            db.session.commit()
            return job

        except Exception as exc:  # noqa: BLE001 - convert to controlled failure state
            logger.exception("AI pipeline failed for recording %s", recording.id)
            job.status = JOB_FAILED
            job.error_message = str(exc)
            recording.status = JOB_FAILED
            db.session.commit()
            raise AIProcessingError(str(exc)) from exc

    def _extract_with_retries(self, recording, request_id) -> HandoffExtractionResult:
        last_error = None
        job = recording.processing_job
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                llm_result = self.llm_provider.generate_json(
                    EXTRACTION_SYSTEM_PROMPT,
                    build_extraction_user_prompt(recording.transcript),
                )
            except Exception as exc:  # provider-level failure (timeout, API error, etc.)
                last_error = exc
                self._log(recording.id, request_id, "LLM", self.llm_provider.name, None,
                           "FAILED", int((time.time() - t0) * 1000), retry_count=attempt)
                job.retry_count = attempt + 1
                db.session.commit()
                continue

            try:
                payload = json.loads(llm_result.raw_text)
                extraction = HandoffExtractionResult.model_validate(payload)
                self._log(recording.id, request_id, "LLM", llm_result.provider, llm_result.model,
                           "SUCCESS", llm_result.duration_ms, llm_result.token_usage,
                           retry_count=attempt, validation_result="VALID")
                job.token_usage = llm_result.token_usage
                job.retry_count = attempt
                db.session.commit()
                return extraction
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                self._log(recording.id, request_id, "LLM", llm_result.provider, llm_result.model,
                           "FAILED", llm_result.duration_ms, llm_result.token_usage,
                           retry_count=attempt, validation_result="INVALID")
                job.retry_count = attempt + 1
                db.session.commit()

        # All retries exhausted: never silently store malformed data.
        raise AIProcessingError(
            f"AI response could not be validated after {self.max_retries + 1} attempt(s): {last_error}"
        )

    def _persist_summaries(self, recording, extraction: HandoffExtractionResult, transcript: str):
        for patient in extraction.patients:
            risk_level, flags = self.risk_service.assess(
                transcript_segment=transcript,
                ai_risk_indicators=patient.risk_indicators,
                ai_risk_level=patient.risk_level,
            )

            summary = PatientSummary(
                recording_id=recording.id,
                patient_name=patient.patient_name,
                bed_number=patient.bed_number,
                condition=patient.condition,
                medications=patient.medications,
                vitals=patient.vitals,
                allergies=patient.allergies,
                pending_tasks=patient.pending_tasks,
                observations=patient.observations,
                risk_level=risk_level,
                ai_confidence=patient.confidence,
                ai_original_payload=patient.model_dump(),
                review_status=REVIEW_PENDING,
            )
            db.session.add(summary)
            db.session.flush()  # obtain summary.id for the risk flags

            for flag in flags:
                db.session.add(RiskFlag(
                    patient_summary_id=summary.id,
                    indicator=flag.indicator,
                    evidence=flag.evidence,
                    source=flag.source,
                    severity_weight=flag.weight,
                ))
        db.session.commit()
