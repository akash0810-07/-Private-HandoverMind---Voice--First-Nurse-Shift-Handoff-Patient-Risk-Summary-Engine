import io
import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import Ward, Nurse


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def ward(db):
    w = Ward(name="ICU")
    db.session.add(w)
    db.session.commit()
    return w


@pytest.fixture()
def nurse(db, ward):
    n = Nurse(full_name="Test Nurse", email="nurse@example.com", role="NURSE", ward_id=ward.id)
    n.set_password("Password123!")
    db.session.add(n)
    db.session.commit()
    return n


@pytest.fixture()
def admin(db):
    a = Nurse(full_name="Admin User", email="admin@example.com", role="ADMIN")
    a.set_password("AdminPass123!")
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture()
def auth_headers(client, nurse):
    resp = client.post("/api/auth/login", json={"email": nurse.email, "password": "Password123!"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client, admin):
    resp = client.post("/api/auth/login", json={"email": admin.email, "password": "AdminPass123!"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def fake_audio_file(name="handoff.wav"):
    return (io.BytesIO(b"FAKE_AUDIO_BYTES_FOR_TESTING"), name)
