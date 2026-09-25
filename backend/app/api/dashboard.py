from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.models import PatientSummary, HandoffRecording
from app.models.summary import RISK_HIGH, RISK_MEDIUM, RISK_LOW, REVIEW_PENDING, REVIEW_CONFIRMED
from app.auth.decorators import get_current_nurse

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/stats")
@jwt_required()
def stats():
    nurse = get_current_nurse()
    claims = get_jwt()

    handoff_query = HandoffRecording.query
    summary_query = PatientSummary.query.join(HandoffRecording)
    if claims.get("role") != "ADMIN":
        handoff_query = handoff_query.filter(HandoffRecording.ward_id == nurse.ward_id)
        summary_query = summary_query.filter(HandoffRecording.ward_id == nurse.ward_id)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    todays_handoffs = handoff_query.filter(HandoffRecording.created_at >= today_start).count()
    total_patients = summary_query.count()
    high_risk = summary_query.filter(PatientSummary.risk_level == RISK_HIGH).count()
    medium_risk = summary_query.filter(PatientSummary.risk_level == RISK_MEDIUM).count()
    low_risk = summary_query.filter(PatientSummary.risk_level == RISK_LOW).count()
    pending_review = summary_query.filter(PatientSummary.review_status == REVIEW_PENDING).count()
    confirmed = summary_query.filter(PatientSummary.review_status == REVIEW_CONFIRMED).count()

    return jsonify({
        "todays_handoffs": todays_handoffs,
        "total_patients": total_patients,
        "high_risk_patients": high_risk,
        "medium_risk_patients": medium_risk,
        "low_risk_patients": low_risk,
        "pending_reviews": pending_review,
        "confirmed_summaries": confirmed,
    })
