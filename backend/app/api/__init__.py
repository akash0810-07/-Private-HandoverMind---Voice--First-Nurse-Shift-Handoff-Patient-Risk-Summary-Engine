def register_blueprints(app):
    from app.auth.routes import bp as auth_bp
    from app.api.handoff import bp as handoff_bp
    from app.api.handoffs_list import bp as handoffs_list_bp
    from app.api.patients import bp as patients_bp
    from app.api.summaries import bp as summaries_bp
    from app.api.jobs import bp as jobs_bp
    from app.api.dashboard import bp as dashboard_bp
    from app.api.admin import bp as admin_bp
    from app.api.system import bp as system_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(handoff_bp)
    app.register_blueprint(handoffs_list_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(summaries_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(system_bp)
