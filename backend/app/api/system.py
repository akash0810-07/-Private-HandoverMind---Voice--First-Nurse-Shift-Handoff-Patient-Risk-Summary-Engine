from flask import Blueprint, jsonify, current_app
from app.extensions import db
from sqlalchemy import text

bp = Blueprint("system", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.get("/ready")
def ready():
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    ready_status = db_ok
    return jsonify({
        "status": "ready" if ready_status else "not_ready",
        "database": "ok" if db_ok else "unreachable",
        "demo_notice": current_app.config.get("DEMO_MODE_BANNER"),
    }), (200 if ready_status else 503)
