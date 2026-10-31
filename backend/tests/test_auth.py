def test_login_success(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "counselor.disha@institution.edu",
        "password": "DishaCounsellor@2026"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["email"] == "counselor.disha@institution.edu"
    assert "counsellor" in data["roles"]
    assert data["campus_id"] == "campus-ipp-01"

def test_login_invalid_password(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "counselor.disha@institution.edu",
        "password": "WrongPassword123"
    })
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]

def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "unknown@institution.edu",
        "password": "Password@2026"
    })
    assert resp.status_code == 401

def test_get_current_user_profile(client, counselor_auth_headers):
    resp = client.get("/api/v1/auth/me", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Dr. Elena Rostova"
    assert "counsellor" in data["roles"]

def test_unauthenticated_request_rejected(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

