import io


def _record_handoff(client, auth_headers):
    data = {"audio": (io.BytesIO(b"FAKE_AUDIO"), "handoff.wav")}
    resp = client.post("/api/handoff/record", headers=auth_headers,
                        data=data, content_type="multipart/form-data")
    assert resp.status_code == 201


def test_dashboard_stats_reflect_recorded_handoff(client, auth_headers):
    _record_handoff(client, auth_headers)
    resp = client.get("/api/dashboard/stats", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["todays_handoffs"] >= 1
    assert body["total_patients"] >= 1
    assert body["pending_reviews"] >= 1


def test_patients_list_supports_risk_filter(client, auth_headers):
    _record_handoff(client, auth_headers)
    resp = client.get("/api/patients?risk=HIGH", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.get_json()["items"]:
        assert item["risk_level"] == "HIGH"


def test_flagged_patients_sorted_high_first(client, auth_headers):
    _record_handoff(client, auth_headers)
    resp = client.get("/api/patients/flagged", headers=auth_headers)
    items = resp.get_json()["items"]
    levels = [i["risk_level"] for i in items]
    assert levels == sorted(levels, key=lambda l: {"HIGH": 0, "MEDIUM": 1}.get(l, 2))


def test_handoffs_history_pagination(client, auth_headers):
    _record_handoff(client, auth_headers)
    resp = client.get("/api/handoffs?page=1&per_page=5", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["page"] == 1
    assert body["total"] >= 1
