import logging
from flask import Flask, jsonify
from app.config import get_config
from app.extensions import db, migrate, jwt, cors, limiter


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    logging.basicConfig(level=logging.INFO)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    from app.auth.routes import is_token_revoked

    @jwt.token_in_blocklist_loader
    def check_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_header, jwt_payload)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_expired", "message": "Your session has expired. Please log in again."}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "token_revoked", "message": "This session has been logged out."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "invalid_token", "message": "Invalid authentication token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return jsonify({"error": "unauthorized", "message": "Authentication is required."}), 401

    # --- Security headers ---
    @app.after_request
    def set_secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        return response

    # --- Blueprints ---
    from app.api import register_blueprints
    register_blueprints(app)

    # --- CLI commands (init-db, create-admin) ---
    from app.cli import register_cli
    register_cli(app)

    # --- Generic error handlers (never leak stack traces) ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "Resource not found."}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "file_too_large", "message": "Uploaded file exceeds the size limit."}), 413

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        return jsonify({"error": "internal_error", "message": "An unexpected error occurred."}), 500

    return app
