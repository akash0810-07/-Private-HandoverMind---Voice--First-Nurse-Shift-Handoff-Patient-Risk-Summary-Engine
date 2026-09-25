"""
Pydantic schemas that define and validate the strict JSON contract the LLM
must return. Any AI output that fails validation is rejected rather than
stored — see AIProcessingPipeline for the retry/reject flow.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


class PatientExtraction(BaseModel):
    patient_name: Optional[str] = None
    bed_number: Optional[str] = None
    condition: Optional[str] = None
    medications: List[str] = Field(default_factory=list)
    vitals: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    pending_tasks: List[str] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    risk_indicators: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"
    confidence: float = 0.5

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v):
        v = (v or "LOW").upper()
        if v not in RISK_LEVELS:
            return "LOW"
        return v

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, v))


class HandoffExtractionResult(BaseModel):
    patients: List[PatientExtraction] = Field(default_factory=list)


class RiskIndicatorEvidence(BaseModel):
    indicator: str
    evidence: Optional[str] = None
    source: str = "AI"  # RULE | AI | HYBRID
