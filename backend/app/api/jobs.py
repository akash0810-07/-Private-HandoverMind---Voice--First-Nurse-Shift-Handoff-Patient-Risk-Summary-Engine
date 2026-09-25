from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.models import ProcessingJob
from app.auth.decorators import get_current_nurse

bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@bp.get("/<job_id>")
@jwt_required()
def get_job(job_id):
    nurse = get_current_nurse()
    claims = get_jwt()
    job = ProcessingJob.query.get(job_id)
    if not job:
        return jsonify({"error": "not_found"}), 404

    if claims.get("role") != "ADMIN" and job.recording.ward_id != nurse.ward_id:
        return jsonify({"error": "forbidden", "message": "Your account does not have access to this ward."}), 403

    return jsonify(job.to_dict())
