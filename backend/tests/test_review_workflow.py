import io


def _record_handoff(client, auth_headers):
    data = {"audio": (io.BytesIO(b"FAKE_AUDIO"), "handoff.wav")}
    resp = client.post("/api/handoff/record", headers=auth_headers,
                        data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    return resp.get_json()["recording_id"]


def test_summary_starts_pending_review(client, auth_headers):
    recording_id = _record_handoff(client, auth_headers)
    resp = client.get(f"/api/handoff/{recording_id}/summary", headers=auth_headers)
    assert resp.status_code == 200
    summaries = resp.get_json()["patient_summaries"]
    assert len(summaries) >= 1
    assert all(s["review_status"] == "PENDING_REVIEW" for s in summaries)
    assert summaries[0]["ai_disclaimer"] == "AI-generated summary — review and confirm before use."


def test_nurse_can_edit_then_confirm_summary(client, auth_headers):
    recording_id = _record_handoff(client, auth_headers)
    summary_id = client.get(f"/api/handoff/{recording_id}/summary",
                             headers=auth_headers).get_json()["patient_summaries"][0]["id"]

    patch_resp = client.patch(f"/api/summaries/{summary_id}", headers=auth_headers,
                               json={"condition": "Corrected condition text"})
    assert patch_resp.status_code == 200
    assert patch_resp.get_json()["condition"] == "Corrected condition text"

    confirm_resp = client.post(f"/api/summaries/{summary_id}/confirm", headers=auth_headers)
    assert confirm_resp.status_code == 200
    body = confirm_resp.get_json()
    assert body["review_status"] == "CONFIRMED"
    assert body["reviewed_by"] == "Test Nurse"


def test_other_ward_cannot_access_summary(client, auth_headers, db):
    from app.models import Ward, Nurse
    other_ward = Ward(name="Other Ward")
    db.session.add(other_ward)
    db.session.commit()
    other_nurse = Nurse(full_name="Other Nurse", email="other@example.com",
                         role="NURSE", ward_id=other_ward.id)
    other_nurse.set_password("Password123!")
    db.session.add(other_nurse)
    db.session.commit()

    recording_id = _record_handoff(client, auth_headers)

    login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "Password123!"})
    other_headers = {"Authorization": f"Bearer {login.get_json()['access_token']}"}

    resp = client.get(f"/api/handoff/{recording_id}/summary", headers=other_headers)
    assert resp.status_code == 403
