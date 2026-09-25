from app.extensions import db
from app.models.base import BaseModel

RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_LEVELS = [RISK_LOW, RISK_MEDIUM, RISK_HIGH]

REVIEW_PENDING = "PENDING_REVIEW"
REVIEW_CONFIRMED = "CONFIRMED"


class PatientSummary(BaseModel):
    __tablename__ = "patient_summaries"

    recording_id = db.Column(
        db.String(36), db.ForeignKey("handoff_recordings.id"), nullable=False
    )

    patient_name = db.Column(db.String(120), nullable=True)
    bed_number = db.Column(db.String(20), nullable=True)
    condition = db.Column(db.Text, nullable=True)

    # JSON list fields (stored as JSON for portability across sqlite/postgres)
    medications = db.Column(db.JSON, default=list)
    vitals = db.Column(db.JSON, default=list)
    allergies = db.Column(db.JSON, default=list)
    pending_tasks = db.Column(db.JSON, default=list)
    observations = db.Column(db.JSON, default=list)

    risk_level = db.Column(db.String(10), default=RISK_LOW, nullable=False)
    ai_confidence = db.Column(db.Float, default=0.0)

    # Human-in-the-loop bookkeeping
    ai_original_payload = db.Column(db.JSON, nullable=True)  # untouched AI output
    review_status = db.Column(db.String(20), default=REVIEW_PENDING, nullable=False)
    reviewed_by_id = db.Column(db.String(36), db.ForeignKey("nurses.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    recording = db.relationship("HandoffRecording", back_populates="patient_summaries")
    reviewed_by = db.relationship("Nurse")
    risk_flags = db.relationship(
        "RiskFlag", back_populates="patient_summary", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "recording_id": self.recording_id,
            "patient_name": self.patient_name,
            "bed_number": self.bed_number,
            "condition": self.condition,
            "medications": self.medications or [],
            "vitals": self.vitals or [],
            "allergies": self.allergies or [],
            "pending_tasks": self.pending_tasks or [],
            "observations": self.observations or [],
            "risk_level": self.risk_level,
            "ai_confidence": self.ai_confidence,
            "review_status": self.review_status,
            "reviewed_by": self.reviewed_by.full_name if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "risk_flags": [f.to_dict() for f in self.risk_flags],
            "ai_disclaimer": "AI-generated summary — review and confirm before use.",
        }


class RiskFlag(BaseModel):
    __tablename__ = "risk_flags"

    patient_summary_id = db.Column(
        db.String(36), db.ForeignKey("patient_summaries.id"), nullable=False
    )
    indicator = db.Column(db.String(200), nullable=False)
    evidence = db.Column(db.Text, nullable=True)  # verbatim transcript snippet
    source = db.Column(db.String(20), nullable=False)  # RULE | AI | HYBRID
    severity_weight = db.Column(db.Float, default=1.0)

    patient_summary = db.relationship("PatientSummary", back_populates="risk_flags")

    def to_dict(self):
        return {
            "id": self.id,
            "indicator": self.indicator,
            "evidence": self.evidence,
            "source": self.source,
            "description": "Potential risk indicator detected in handoff.",
        }


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    actor_id = db.Column(db.String(36), db.ForeignKey("nurses.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.String(36))
    details = db.Column(db.JSON, default=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "created_at": self.created_at.isoformat(),
        }


class AIProcessingLog(BaseModel):
    """Observability record for every AI/STT call made by the pipeline."""
    __tablename__ = "ai_processing_logs"

    recording_id = db.Column(db.String(36), db.ForeignKey("handoff_recordings.id"))
    request_id = db.Column(db.String(36), nullable=False)
    stage = db.Column(db.String(30))  # STT | LLM | RISK
    provider = db.Column(db.String(50))
    model = db.Column(db.String(80))
    status = db.Column(db.String(20))  # SUCCESS | FAILED | RETRY
    duration_ms = db.Column(db.Integer)
    token_usage = db.Column(db.Integer, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    validation_result = db.Column(db.String(20), nullable=True)  # VALID | INVALID

    def to_dict(self):
        return {
            "id": self.id,
            "recording_id": self.recording_id,
            "request_id": self.request_id,
            "stage": self.stage,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
            "validation_result": self.validation_result,
            "created_at": self.created_at.isoformat(),
        }
