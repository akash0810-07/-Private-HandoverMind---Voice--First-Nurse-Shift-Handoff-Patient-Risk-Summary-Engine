from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.models import PatientSummary, HandoffRecording
from app.auth.decorators import get_current_nurse

bp = Blueprint("patients", __name__, url_prefix="/api/patients")

_RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _ward_scoped_query(claims, nurse):
    query = PatientSummary.query.join(HandoffRecording)
    if claims.get("role") != "ADMIN":
        query = query.filter(HandoffRecording.ward_id == nurse.ward_id)
    return query


@bp.get("")
@jwt_required()
def list_patients():
    nurse = get_current_nurse()
    claims = get_jwt()
    query = _ward_scoped_query(claims, nurse)

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(
            (PatientSummary.patient_name.ilike(like)) | (PatientSummary.bed_number.ilike(like))
        )

    risk = request.args.get("risk")
    if risk:
        query = query.filter(PatientSummary.risk_level == risk.upper())

    review_status = request.args.get("review_status")
    if review_status:
        query = query.filter(PatientSummary.review_status == review_status.upper())

    sort = request.args.get("sort", "risk")  # risk | latest
    results = query.all()
    if sort == "risk":
        results.sort(key=lambda p: (_RISK_ORDER.get(p.risk_level, 3), -p.created_at.timestamp()))
    else:
        results.sort(key=lambda p: p.created_at, reverse=True)

    return jsonify({"items": [p.to_dict() for p in results]})


@bp.get("/flagged")
@jwt_required()
def flagged_patients():
    """High and medium risk patients, high-risk first — the primary
    triage view for an incoming nurse."""
    nurse = get_current_nurse()
    claims = get_jwt()
    query = _ward_scoped_query(claims, nurse).filter(
        PatientSummary.risk_level.in_(["HIGH", "MEDIUM"])
    )
    results = query.all()
    results.sort(key=lambda p: (_RISK_ORDER.get(p.risk_level, 3), -p.created_at.timestamp()))
    return jsonify({"items": [p.to_dict() for p in results]})


@bp.get("/<patient_id>")
@jwt_required()
def get_patient(patient_id):
    nurse = get_current_nurse()
    claims = get_jwt()
    summary = PatientSummary.query.get(patient_id)
    if not summary:
        return jsonify({"error": "not_found"}), 404

    if claims.get("role") != "ADMIN" and summary.recording.ward_id != nurse.ward_id:
        return jsonify({"error": "forbidden", "message": "Your account does not have access to this ward."}), 403

    return jsonify(summary.to_dict())
