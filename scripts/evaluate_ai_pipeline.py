"""
Deterministic evaluation harness for the AI pipeline, using a fixed set of
synthetic handoff transcripts with known expected extractions. Run this to
produce the metrics referenced in docs/architecture.md (structured
extraction accuracy, risk flag recall, processing latency).

This does NOT call any external API — it evaluates whichever provider is
configured via STT_PROVIDER/LLM_PROVIDER (mock by default), so it is safe
to run in CI.

Usage:
    cd backend
    python ../scripts/evaluate_ai_pipeline.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app
from app.extensions import db
from app.models import Ward, Nurse, HandoffRecording
from app.services.ai.factory import get_llm_provider
from app.services.ai.pipeline import AIProcessingPipeline
from app.services.stt.base import STTProvider, TranscriptionResult

CASES = [
    {
        "transcript": "Bed 12 is Mr Sharma. He has pneumonia. He is allergic to penicillin. "
                      "He complained of breathing difficulty. Blood test is pending.",
        "expected_risk_level": "HIGH",
        "expected_min_flags": 2,
    },
    {
        "transcript": "Bed 4, Mrs Verma, recovering from hip surgery. Vitals stable. No known allergies.",
        "expected_risk_level": "LOW",
        "expected_min_flags": 0,
    },
    {
        "transcript": "Bed 7 is Mr Iyer. He reported dizziness and mild confusion. CT scan pending.",
        "expected_risk_level": "MEDIUM",
        "expected_min_flags": 1,
    },
]


class FixedTranscriptSTTProvider(STTProvider):
    """Test-only STT stand-in that returns a predetermined transcript,
    so this evaluation exercises the LLM + risk-detection stages against
    known, hand-labelled input rather than depending on STT behavior."""
    name = "fixed_transcript_eval"

    def __init__(self, transcript: str):
        self._transcript = transcript

    def transcribe(self, audio_path: str, content_type: str) -> TranscriptionResult:
        return TranscriptionResult(
            transcript=self._transcript, provider=self.name, duration_ms=0, raw_meta={}
        )


def run():
    app = create_app()
    with app.app_context():
        db.create_all()
        ward = Ward.query.first() or Ward(name="Eval Ward")
        if not ward.id:
            db.session.add(ward)
            db.session.commit()
        nurse = Nurse.query.first()
        if not nurse:
            nurse = Nurse(full_name="Eval Nurse", email="eval@example.com", role="NURSE", ward_id=ward.id)
            nurse.set_password("x")
            db.session.add(nurse)
            db.session.commit()

        total = len(CASES)
        risk_level_matches = 0
        recall_hits = 0
        latencies = []

        for i, case in enumerate(CASES):
            pipeline = AIProcessingPipeline(
                stt_provider=FixedTranscriptSTTProvider(case["transcript"]),
                llm_provider=get_llm_provider(),
            )
            recording = HandoffRecording(ward_id=ward.id, recorded_by_id=nurse.id)
            db.session.add(recording)
            db.session.commit()

            start = time.time()
            job = pipeline.run(recording, audio_path="unused", content_type="text/plain")
            latency = time.time() - start
            latencies.append(latency)

            summaries = recording.patient_summaries
            if not summaries:
                print(f"[Case {i+1}] FAILED — no summary produced")
                continue

            summary = summaries[0]
            level_ok = summary.risk_level == case["expected_risk_level"]
            flags_ok = len(summary.risk_flags) >= case["expected_min_flags"]
            risk_level_matches += int(level_ok)
            recall_hits += int(flags_ok)

            print(f"[Case {i+1}] risk_level={summary.risk_level} "
                  f"(expected {case['expected_risk_level']}) "
                  f"flags={len(summary.risk_flags)} (expected >= {case['expected_min_flags']}) "
                  f"latency={latency:.2f}s status={job.status}")

        print()
        print(f"Risk level accuracy: {risk_level_matches}/{total}")
        print(f"Risk flag recall target met: {recall_hits}/{total}")
        print(f"Average processing latency: {sum(latencies)/len(latencies):.2f}s "
              f"(target <= 15s per spec)")


if __name__ == "__main__":
    run()
