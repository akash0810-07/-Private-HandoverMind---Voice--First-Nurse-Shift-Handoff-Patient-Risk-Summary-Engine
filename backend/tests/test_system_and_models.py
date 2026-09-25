def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_ready_endpoint(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ready"
    assert "Academic demonstration system" in body["demo_notice"]


def test_nurse_password_hash_is_not_plaintext(db, nurse):
    assert nurse.password_hash != "Password123!"
    assert nurse.check_password("Password123!")
    assert not nurse.check_password("wrong-password")


def test_ward_nurse_relationship(db, ward, nurse):
    assert nurse.ward_id == ward.id
    assert nurse in ward.nurses
