"""
Role-based and ward-level access control decorators.

These wrap Flask view functions. They assume the JWT has already been
verified (use alongside @jwt_required()) and read custom claims placed on
the token at login time (see app/auth/routes.py).
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from app.models import Nurse


def get_current_nurse():
    nurse_id = get_jwt_identity()
    if not nurse_id:
        return None
    return Nurse.query.get(nurse_id)


def roles_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return jsonify({
                    "error": "forbidden",
                    "message": "Your account does not have access to this resource."
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def ward_access_required(ward_id_param="ward_id"):
    """
    Ensures the authenticated nurse may only access data scoped to their
    own ward, unless they are an ADMIN (who may access any ward).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") == "ADMIN":
                return fn(*args, **kwargs)

            requested_ward_id = kwargs.get(ward_id_param)
            token_ward_id = claims.get("ward_id")

            if requested_ward_id and requested_ward_id != token_ward_id:
                return jsonify({
                    "error": "forbidden",
                    "message": "Your account does not have access to this ward."
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
