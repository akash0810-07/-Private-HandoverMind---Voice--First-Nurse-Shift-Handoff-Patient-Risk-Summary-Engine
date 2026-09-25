from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from marshmallow import ValidationError

from app.extensions import db
from app.models import PatientSummary, AuditLog
from app.models.summary import REVIEW_CONFIRMED
from app.auth.decorators import get_current_nurse
from app.schemas.api_schema import PatientSummaryUpdateSchema

bp = Blueprint("summaries", __name__, url_prefix="/api/summaries")

_update_schema = PatientSummaryUpdateSchema()

EDITABLE_FIELDS = [
    "patient_name", "bed_number", "condition", "medications", "vitals",
    "allergies", "pending_tasks", "observations", "risk_level",
]


def _check_ward_access(summary, claims, nurse):
    return claims.get("role") == "ADMIN" or summary.recording.ward_id == nurse.ward_id


@bp.patch("/<summary_id>")
@jwt_required()
def edit_summary(summary_id):
    """
    Lets a nurse correct the AI-generated summary before confirming it.
    The original AI output is preserved separately (ai_original_payload)
    so it's always clear what the AI produced vs. what a human edited.
    """
    nurse = get_current_nurse()
    claims = get_jwt()
    summary = PatientSummary.query.get(summary_id)
    if not summary:
        return jsonify({"error": "not_found"}), 404
    if not _check_ward_access(summary, claims, nurse):
        return jsonify({"error": "forbidden", "message": "Your account does not have access to this ward."}), 403

    try:
        data = _update_schema.load(request.get_json(silent=True) or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": "validation_error", "message": err.messages}), 400

    for field in EDITABLE_FIELDS:
        if field in data:
            setattr(summary, field, data[field])

    db.session.add(AuditLog(
        actor_id=nurse.id, action="SUMMARY_EDITED",
        resource_type="PatientSummary", resource_id=summary.id, details=data,
    ))
    db.session.commit()
    return jsonify(summary.to_dict())


@bp.post("/<summary_id>/confirm")
@jwt_required()
def confirm_summary(summary_id):
    """
    Marks a summary as human-reviewed/confirmed. This is mandatory before
    a summary should be treated as reliable for the next shift — an
    AI-generated summary is never presented as final without this step.
    """
    nurse = get_current_nurse()
    claims = get_jwt()
    summary = PatientSummary.query.get(summary_id)
    if not summary:
        return jsonify({"error": "not_found"}), 404
    if not _check_ward_access(summary, claims, nurse):
        return jsonify({"error": "forbidden", "message": "Your account does not have access to this ward."}), 403

    summary.review_status = REVIEW_CONFIRMED
    summary.reviewed_by_id = nurse.id
    summary.reviewed_at = datetime.now(timezone.utc)

    db.session.add(AuditLog(
        actor_id=nurse.id, action="SUMMARY_CONFIRMED",
        resource_type="PatientSummary", resource_id=summary.id,
    ))
    db.session.commit()
    return jsonify(summary.to_dict())
