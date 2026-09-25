import json
import pytest
from pydantic import ValidationError

from app.schemas.ai_schema import HandoffExtractionResult
from app.services.ai.mock_llm_provider import MockLLMProvider
from app.services.stt.mock_provider import MockSTTProvider
from app.services.ai.pipeline import AIProcessingPipeline, AIProcessingError
from app.services.ai.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt
from app.models import HandoffRecording, Ward, Nurse
from app.extensions import db


def test_schema_rejects_invalid_risk_level_by_defaulting_to_low():
    result = HandoffExtractionResult.model_validate({
        "patients": [{"risk_level": "CATASTROPHIC"}]
    })
    assert result.patients[0].risk_level == "LOW"


def test_schema_clamps_confidence_out_of_range():
    result = HandoffExtractionResult.model_validate({
        "patients": [{"confidence": 5.0}]
    })
    assert result.patients[0].confidence == 1.0


def test_schema_rejects_missing_patients_key_gracefully():
    result = HandoffExtractionResult.model_validate({})
    assert result.patients == []


def test_mock_llm_returns_valid_json_matching_schema():
    provider = MockLLMProvider()
    transcript = ("Bed 12 is Mr Sharma. He has pneumonia. He is allergic to penicillin. "
                  "Blood test is pending.")
    result = provider.generate_json(EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt(transcript))
    payload = json.loads(result.raw_text)
    parsed = HandoffExtractionResult.model_validate(payload)
    assert len(parsed.patients) >= 1
    assert parsed.patients[0].bed_number == "12"


class _AlwaysBadLLMProvider:
    name = "always_bad"

    def generate_json(self, system_prompt, user_prompt):
        from app.services.ai.base import LLMResult
        return LLMResult(raw_text="not json at all", provider=self.name, model="bad", duration_ms=1)


def test_pipeline_raises_controlled_error_on_persistent_malformed_output(app, db):
    ward = Ward(name="Ward A")
    db.session.add(ward)
    db.session.commit()
    nurse = Nurse(full_name="N", email="n@example.com", role="NURSE", ward_id=ward.id)
    nurse.set_password("x")
    db.session.add(nurse)
    db.session.commit()

    recording = HandoffRecording(ward_id=ward.id, recorded_by_id=nurse.id)
    db.session.add(recording)
    db.session.commit()

    pipeline = AIProcessingPipeline(
        stt_provider=MockSTTProvider(),
        llm_provider=_AlwaysBadLLMProvider(),
        max_retries=1,
    )

    with pytest.raises(AIProcessingError):
        pipeline.run(recording, audio_path="/tmp/does-not-matter", content_type="audio/wav")

    assert recording.status == "FAILED"


def test_pipeline_end_to_end_with_mock_providers_persists_summaries(app, db):
    ward = Ward(name="Ward B")
    db.session.add(ward)
    db.session.commit()
    nurse = Nurse(full_name="N2", email="n2@example.com", role="NURSE", ward_id=ward.id)
    nurse.set_password("x")
    db.session.add(nurse)
    db.session.commit()

    recording = HandoffRecording(ward_id=ward.id, recorded_by_id=nurse.id)
    db.session.add(recording)
    db.session.commit()

    pipeline = AIProcessingPipeline(stt_provider=MockSTTProvider(), llm_provider=MockLLMProvider())
    job = pipeline.run(recording, audio_path="/tmp/does-not-matter", content_type="audio/wav")

    assert job.status == "COMPLETED"
    assert recording.status == "COMPLETED"
    assert recording.transcript is not None
    assert len(recording.patient_summaries) >= 1
    for summary in recording.patient_summaries:
        assert summary.review_status == "PENDING_REVIEW"
