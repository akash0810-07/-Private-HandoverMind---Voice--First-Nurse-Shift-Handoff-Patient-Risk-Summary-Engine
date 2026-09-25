from app.extensions import db
from app.models.base import BaseModel

# Processing job states
JOB_QUEUED = "QUEUED"
JOB_TRANSCRIBING = "TRANSCRIBING"
JOB_ANALYSING = "ANALYSING"
JOB_RISK_DETECTION = "RISK_DETECTION"
JOB_COMPLETED = "COMPLETED"
JOB_FAILED = "FAILED"

JOB_STATES = [
    JOB_QUEUED,
    JOB_TRANSCRIBING,
    JOB_ANALYSING,
    JOB_RISK_DETECTION,
    JOB_COMPLETED,
    JOB_FAILED,
]


class HandoffRecording(BaseModel):
    __tablename__ = "handoff_recordings"

    ward_id = db.Column(db.String(36), db.ForeignKey("wards.id"), nullable=False)
    recorded_by_id = db.Column(db.String(36), db.ForeignKey("nurses.id"), nullable=False)

    audio_location = db.Column(db.String(500), nullable=True)  # storage key/path
    audio_content_type = db.Column(db.String(100), nullable=True)
    audio_duration_seconds = db.Column(db.Float, nullable=True)

    transcript = db.Column(db.Text, nullable=True)
    transcript_provider = db.Column(db.String(50), nullable=True)

    status = db.Column(db.String(30), default=JOB_QUEUED, nullable=False)

    ward = db.relationship("Ward", back_populates="recordings")
    recorded_by = db.relationship("Nurse")
    patient_summaries = db.relationship(
        "PatientSummary", back_populates="recording", cascade="all, delete-orphan"
    )
    processing_job = db.relationship(
        "ProcessingJob", back_populates="recording", uselist=False,
        cascade="all, delete-orphan"
    )

    def to_dict(self, include_summaries=False):
        data = {
            "id": self.id,
            "ward_id": self.ward_id,
            "recorded_by": self.recorded_by.full_name if self.recorded_by else None,
            "status": self.status,
            "transcript": self.transcript,
            "audio_duration_seconds": self.audio_duration_seconds,
            "created_at": self.created_at.isoformat(),
        }
        if include_summaries:
            data["patient_summaries"] = [p.to_dict() for p in self.patient_summaries]
        return data


class ProcessingJob(BaseModel):
    """Tracks the async-style AI pipeline execution for one recording."""
    __tablename__ = "processing_jobs"

    recording_id = db.Column(
        db.String(36), db.ForeignKey("handoff_recordings.id"), nullable=False, unique=True
    )
    status = db.Column(db.String(30), default=JOB_QUEUED, nullable=False)
    stt_provider = db.Column(db.String(50))
    llm_provider = db.Column(db.String(50))
    llm_model = db.Column(db.String(80))
    prompt_version = db.Column(db.String(50))
    retry_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    token_usage = db.Column(db.Integer, nullable=True)

    recording = db.relationship("HandoffRecording", back_populates="processing_job")

    def to_dict(self):
        return {
            "id": self.id,
            "recording_id": self.recording_id,
            "status": self.status,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "updated_at": self.updated_at.isoformat(),
        }
