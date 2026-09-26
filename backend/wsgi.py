from dotenv import load_dotenv
load_dotenv()

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402

app = create_app()

# Boot-time convenience for deployments with no separate shell/console step
# (e.g. Render's Docker web service). Disabled unless explicitly enabled via
# AUTO_CREATE_TABLES / AUTO_SEED_DEMO_DATA — both are idempotent (db.create_all
# is a no-op if tables exist; seed_demo_data skips if a Ward already exists),
# so it's safe even with multiple gunicorn workers booting concurrently.
with app.app_context():
    if app.config.get("AUTO_CREATE_TABLES"):
        db.create_all()
    if app.config.get("AUTO_SEED_DEMO_DATA"):
        from app.seed import seed_demo_data
        seed_demo_data(verbose=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
