"""
Mock LLM provider used for offline development, CI, and demos when no
LLM_PROVIDER API key is configured. It performs a lightweight, transparent
segmentation + extraction over the transcript text so the rest of the
pipeline (validation, risk detection, human review) can be exercised
end-to-end without any external API calls.

This is intentionally simple and clearly labelled as a mock — it is not
presented anywhere as a real clinical NLP model.
"""
import json
import re
import time
from app.services.ai.base import LLMProvider, LLMResult

_VITAL_PATTERN = re.compile(r"(temperature|bp|blood pressure|pulse|heart rate|spo2|oxygen)[^.]*", re.I)
_ALLERGY_PATTERN = re.compile(r"allerg(?:y|ic)[^.]*", re.I)
_MED_PATTERN = re.compile(r"(antibiotic|paracetamol|medication|given|dose|mg)[^.]*", re.I)
_PENDING_PATTERN = re.compile(r"(pending|scheduled|awaiting)[^.]*", re.I)
_RISK_KEYWORDS = [
    "breathing difficulty", "fall", "confusion", "dizziness", "deteriorat",
    "severe pain", "allerg", "abnormal", "elevated", "unresponsive",
]


def _extract_name_and_bed(segment: str):
    bed_match = re.search(r"bed\s*(\w+)", segment, re.I)
    name_match = re.search(r"(?:is|,)\s*(Mr|Mrs|Ms|Dr)\.?\s+([A-Z][a-zA-Z]+)", segment)
    bed = bed_match.group(1) if bed_match else None
    name = f"{name_match.group(1)} {name_match.group(2)}" if name_match else None
    return name, bed


def _split_into_patient_segments(transcript: str):
    # Split on "Bed <n>" markers as a simple heuristic for multi-patient transcripts.
    parts = re.split(r"(?=Bed\s+\w+)", transcript, flags=re.I)
    parts = [p.strip() for p in parts if p.strip()]
    return parts or [transcript]


def _extract_list(pattern, segment):
    return [m.strip(" .") for m in pattern.findall(segment)][:5]


class MockLLMProvider(LLMProvider):
    name = "mock"

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        start = time.time()
        # The transcript is embedded between --- markers in the user prompt.
        match = re.search(r"---\n(.*)\n---", user_prompt, re.S)
        transcript = match.group(1) if match else user_prompt

        patients = []
        for segment in _split_into_patient_segments(transcript):
            name, bed = _extract_name_and_bed(segment)
            condition_match = re.search(r"has\s+([a-zA-Z ]+?)\.", segment)
            condition = condition_match.group(1).strip() if condition_match else None

            risk_hits = [kw for kw in _RISK_KEYWORDS if kw in segment.lower()]
            allergies = _extract_list(_ALLERGY_PATTERN, segment)
            if allergies:
                risk_hits.append("medication allergy")

            if len(risk_hits) >= 2:
                risk_level = "HIGH"
            elif len(risk_hits) == 1:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            patients.append({
                "patient_name": name,
                "bed_number": bed,
                "condition": condition,
                "medications": _extract_list(_MED_PATTERN, segment),
                "vitals": _extract_list(_VITAL_PATTERN, segment),
                "allergies": allergies,
                "pending_tasks": _extract_list(_PENDING_PATTERN, segment),
                "observations": [],
                "risk_indicators": risk_hits,
                "risk_level": risk_level,
                "confidence": 0.6 if name else 0.35,
            })

        payload = {"patients": patients}
        duration_ms = int((time.time() - start) * 1000) + 150  # simulate latency
        return LLMResult(
            raw_text=json.dumps(payload),
            provider=self.name,
            model="mock-extractor-v1",
            duration_ms=duration_ms,
            token_usage=None,
        )
