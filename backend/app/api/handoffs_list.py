from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.models import HandoffRecording
from app.auth.decorators import get_current_nurse

bp = Blueprint("handoffs_list", __name__, url_prefix="/api/handoffs")


@bp.get("")
@jwt_required()
def list_handoffs():
    nurse = get_current_nurse()
    claims = get_jwt()

    query = HandoffRecording.query
    if claims.get("role") != "ADMIN":
        query = query.filter_by(ward_id=nurse.ward_id)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = query.order_by(HandoffRecording.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [r.to_dict() for r in pagination.items],
        "page": page,
        "per_page": per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })
