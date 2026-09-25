"""
Deletes handoff recordings (and their audio files) older than
AUDIO_RETENTION_DAYS. Intended to be run periodically (e.g. a nightly
cron job or scheduled GitHub Action) to satisfy the project's configurable
data-retention requirement for synthetic demo recordings.

Usage:
    cd backend
    python ../scripts/cleanup_recordings.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app
from app.extensions import db
from app.models import HandoffRecording
from app.services.storage.factory import get_storage_backend


def run():
    app = create_app()
    with app.app_context():
        retention_days = app.config.get("AUDIO_RETENTION_DAYS", 30)
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        old_recordings = HandoffRecording.query.filter(HandoffRecording.created_at < cutoff).all()
        storage = get_storage_backend()

        deleted = 0
        for recording in old_recordings:
            if recording.audio_location:
                try:
                    storage.delete(recording.audio_location)
                except OSError:
                    pass
            db.session.delete(recording)
            deleted += 1

        db.session.commit()
        print(f"Deleted {deleted} recording(s) older than {retention_days} days.")


if __name__ == "__main__":
    run()
