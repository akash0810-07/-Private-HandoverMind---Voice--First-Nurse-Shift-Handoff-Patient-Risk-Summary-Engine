import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db, limiter
from app.models import HandoffRecording, ProcessingJob, AuditLog
from app.auth.decorators import get_current_nurse
from app.services.storage.factory import get_storage_backend
from app.services.ai.factory import get_stt_provider, get_llm_provider
from app.services.ai.pipeline import AIProcessingPipeline, AIProcessingError

bp = Blueprint("handoff", __name__, url_prefix="/api/handoff")


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_AUDIO_EXTENSIONS"]


@bp.post("/record")
@jwt_required()
@limiter.limit("20 per hour")
def record_handoff():
    """
    Accepts a multipart audio upload, stores it, creates a HandoffRecording
    + ProcessingJob, and synchronously runs the AI pipeline (STT -> LLM ->
    risk detection -> pending-review summaries). The frontend can poll
    GET /api/jobs/:id for stage-by-stage progress, mirroring an async flow.
    """
    nurse = get_current_nurse()
    if not nurse:
        return jsonify({"error": "unauthorized"}), 401
    if not nurse.ward_id:
        return jsonify({"error": "validation_error", "message": "Nurse has no assigned ward."}), 400

    if "audio" not in request.files:
        return jsonify({"error": "validation_error", "message": "No audio file provided."}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "validation_error", "message": "Empty filename."}), 400

    if not _allowed_file(audio_file.filename):
        return jsonify({
            "error": "validation_error",
            "message": f"Unsupported audio type. Allowed: {sorted(current_app.config['ALLOWED_AUDIO_EXTENSIONS'])}"
        }), 400

    storage = get_storage_backend()
    try:
        location = storage.save(audio_file, audio_file.filename)
    except OSError as exc:
        return jsonify({"error": "storage_failure", "message": "Could not store audio file."}), 502

    recording = HandoffRecording(
        ward_id=nurse.ward_id,
        recorded_by_id=nurse.id,
        audio_location=location,
        audio_content_type=audio_file.mimetype,
    )
    db.session.add(recording)
    db.session.commit()

    job = ProcessingJob(recording_id=recording.id)
    db.session.add(job)
    db.session.add(AuditLog(
        actor_id=nurse.id, action="HANDOFF_RECORDED",
        resource_type="HandoffRecording", resource_id=recording.id,
    ))
    db.session.commit()

    pipeline = AIProcessingPipeline(
        stt_provider=get_stt_provider(),
        llm_provider=get_llm_provider(),
        max_retries=current_app.config.get("AI_MAX_RETRIES", 2),
    )

    audio_path = storage.get_path(location)
    try:
        pipeline.run(recording, audio_path, audio_file.mimetype)
    except AIProcessingError as exc:
        return jsonify({
            "error": "ai_processing_failed",
            "message": "AI analysis could not be completed. The transcript has been saved for retry.",
            "recording_id": recording.id,
            "job_id": job.id,
            "detail": str(exc),
        }), 502

    return jsonify({
        "recording_id": recording.id,
        "job_id": job.id,
        "status": recording.status,
    }), 201


@bp.get("/<recording_id>/summary")
@jwt_required()
def get_handoff_summary(recording_id):
    nurse = get_current_nurse()
    recording = HandoffRecording.query.get(recording_id)
    if not recording:
        return jsonify({"error": "not_found"}), 404

    claims = get_jwt()
    if claims.get("role") != "ADMIN" and recording.ward_id != nurse.ward_id:
        return jsonify({"error": "forbidden", "message": "Your account does not have access to this ward."}), 403

    return jsonify(recording.to_dict(include_summaries=True))
