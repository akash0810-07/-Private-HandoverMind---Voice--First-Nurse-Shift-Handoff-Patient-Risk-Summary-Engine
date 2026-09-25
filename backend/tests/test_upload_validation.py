import io
from tests.conftest import fake_audio_file


def test_upload_rejects_unsupported_extension(client, auth_headers):
    data = {"audio": (io.BytesIO(b"not audio"), "handoff.txt")}
    resp = client.post("/api/handoff/record", headers=auth_headers,
                        data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_upload_rejects_missing_file(client, auth_headers):
    resp = client.post("/api/handoff/record", headers=auth_headers,
                        data={}, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_upload_requires_auth(client):
    file_obj, name = fake_audio_file()
    data = {"audio": (file_obj, name)}
    resp = client.post("/api/handoff/record", data=data, content_type="multipart/form-data")
    assert resp.status_code == 401


def test_upload_success_runs_pipeline_with_mock_providers(client, auth_headers, app):
    file_obj, name = fake_audio_file()
    data = {"audio": (file_obj, name)}
    resp = client.post("/api/handoff/record", headers=auth_headers,
                        data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "COMPLETED"
    assert "recording_id" in body
