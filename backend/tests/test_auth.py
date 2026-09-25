def test_login_success(client, nurse):
    resp = client.post("/api/auth/login", json={"email": "nurse@example.com", "password": "Password123!"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert "access_token" in body
    assert body["nurse"]["email"] == "nurse@example.com"


def test_login_wrong_password(client, nurse):
    resp = client.post("/api/auth/login", json={"email": "nurse@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post("/api/auth/login", json={"email": ""})
    assert resp.status_code == 400


def test_protected_route_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_nurse(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "nurse@example.com"


def test_admin_only_route_forbidden_for_nurse(client, auth_headers):
    resp = client.get("/api/admin/wards", headers=auth_headers)
    assert resp.status_code == 403


def test_admin_only_route_allowed_for_admin(client, admin_headers):
    resp = client.get("/api/admin/wards", headers=admin_headers)
    assert resp.status_code == 200


def test_logout_revokes_token(client, auth_headers):
    resp = client.post("/api/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
    resp2 = client.get("/api/auth/me", headers=auth_headers)
    assert resp2.status_code == 401
