from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from app.extensions import db, limiter
from app.models import Nurse, AuditLog

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory revocation set for logout (a production deployment would use
# Redis; kept simple and documented here for the academic scope of v1).
_revoked_tokens = set()


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "validation_error", "message": "Email and password are required."}), 400

    nurse = Nurse.query.filter_by(email=email).first()
    if not nurse or not nurse.is_active or not nurse.check_password(password):
        return jsonify({"error": "invalid_credentials", "message": "Invalid email or password."}), 401

    claims = {"role": nurse.role, "ward_id": nurse.ward_id}
    access_token = create_access_token(identity=nurse.id, additional_claims=claims)
    refresh_token = create_refresh_token(identity=nurse.id, additional_claims=claims)

    db.session.add(AuditLog(actor_id=nurse.id, action="LOGIN", resource_type="Nurse", resource_id=nurse.id))
    db.session.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "nurse": nurse.to_dict(),
    })


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    new_claims = {"role": claims.get("role"), "ward_id": claims.get("ward_id")}
    access_token = create_access_token(identity=identity, additional_claims=new_claims)
    return jsonify({"access_token": access_token})


@bp.post("/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    _revoked_tokens.add(jti)
    return jsonify({"message": "Logged out."})


@bp.get("/me")
@jwt_required()
def me():
    nurse = Nurse.query.get(get_jwt_identity())
    if not nurse:
        return jsonify({"error": "not_found"}), 404
    return jsonify(nurse.to_dict())


def is_token_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in _revoked_tokens
