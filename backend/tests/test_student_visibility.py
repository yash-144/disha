def test_list_assigned_students(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    names = [s["display_name"] for s in data["items"]]
    assert "Ana Silva" in names

def test_search_assigned_students_by_name(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students?search=Ana", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["display_name"] == "Ana Silva"

def test_search_assigned_students_by_id(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students?search=9070", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["external_ref"] == "STU-2024-9070"

def test_view_student_profile(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students/student-001", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Ana Silva"
    assert data["course"] == "Software Engineering (Code 9070)"
    assert len(data["assigned_cases"]) >= 1

def test_view_student_observations(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students/student-001/observations", headers=counselor_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 2
    domains = [obs["domain"] for obs in items]
    assert "attendance" in domains
    assert "academic" in domains
    assert items[0]["provenance"] != ""

def test_view_student_support_history(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/students/student-001/support-history", headers=counselor_auth_headers)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) >= 1
    assert history[0]["case_id"] == "case-101"

