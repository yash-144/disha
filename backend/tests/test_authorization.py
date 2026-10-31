def test_faculty_role_denied_counsellor_dashboard(client, faculty_auth_headers):
    resp = client.get("/api/v1/counsellor/dashboard", headers=faculty_auth_headers)
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]

def test_faculty_role_denied_cases(client, faculty_auth_headers):
    resp = client.get("/api/v1/cases", headers=faculty_auth_headers)
    assert resp.status_code == 403

def test_counsellor_cannot_accept_another_counsellors_case(client, other_counselor_auth_headers):
    # case-101 is assigned to Elena (user-counselor-01). Marcus Vance (user-counselor-02) tries to accept it
    resp = client.post("/api/v1/cases/case-101/accept", headers=other_counselor_auth_headers, json={
        "expected_version": 1
    })
    assert resp.status_code == 403
    assert "assigned counsellor" in resp.json()["error"]

def test_counsellor_cannot_view_unauthorized_case_details(client, other_counselor_auth_headers):
    resp = client.get("/api/v1/cases/case-101", headers=other_counselor_auth_headers)
    assert resp.status_code == 403

def test_counsellor_cannot_close_unauthorized_case(client, other_counselor_auth_headers):
    resp = client.post("/api/v1/cases/case-101/close", headers=other_counselor_auth_headers, json={
        "expected_version": 1,
        "reason_code": "TAMPER_ATTEMPT",
        "closing_notes": "Unauthorized attempt"
    })
    assert resp.status_code == 403

def test_campus_tenancy_isolation(client, counselor_auth_headers):
    # Request with a different foreign campus ID
    headers = {
        **counselor_auth_headers,
        "X-Campus-ID": "campus-foreign-99"
    }
    resp = client.get("/api/v1/cases/case-101", headers=headers)
    assert resp.status_code == 403
    assert "campus tenancy" in resp.json()["error"]

def test_missing_campus_identifier_rejected(client):
    # Valid token structure without campus
    resp = client.get("/api/v1/counsellor/dashboard", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 401

