from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Ward, Nurse
from app.auth.decorators import roles_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/wards")
@jwt_required()
@roles_required("ADMIN")
def list_wards():
    return jsonify({"items": [w.to_dict() for w in Ward.query.all()]})


@bp.post("/wards")
@jwt_required()
@roles_required("ADMIN")
def create_ward():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "validation_error", "message": "Ward name is required."}), 400
    if Ward.query.filter_by(name=name).first():
        return jsonify({"error": "conflict", "message": "A ward with this name already exists."}), 409
    ward = Ward(name=name, description=data.get("description"))
    db.session.add(ward)
    db.session.commit()
    return jsonify(ward.to_dict()), 201


@bp.get("/nurses")
@jwt_required()
@roles_required("ADMIN")
def list_nurses():
    return jsonify({"items": [n.to_dict() for n in Nurse.query.all()]})


@bp.patch("/nurses/<nurse_id>/ward")
@jwt_required()
@roles_required("ADMIN")
def assign_ward(nurse_id):
    data = request.get_json(silent=True) or {}
    nurse = Nurse.query.get(nurse_id)
    if not nurse:
        return jsonify({"error": "not_found"}), 404
    ward = Ward.query.get(data.get("ward_id"))
    if not ward:
        return jsonify({"error": "validation_error", "message": "Invalid ward_id."}), 400
    nurse.ward_id = ward.id
    db.session.commit()
    return jsonify(nurse.to_dict())
