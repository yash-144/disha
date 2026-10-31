def test_counsellor_dashboard_full(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/dashboard", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    summary = data["summary"]
    
    # 3 pre-seeded cases assigned to Elena (case-101: ASSIGNED, case-102: SUPPORT_IN_PROGRESS, case-103: ACCEPTED & overdue)
    assert summary["assigned_cases_count"] == 3
    assert summary["assigned_students_count"] == 3
    assert summary["pending_cases_count"] == 1 # case-101
    assert summary["active_cases_count"] >= 1  # case-102 (SUPPORT_IN_PROGRESS), case-103 (ACCEPTED)
    assert summary["overdue_cases_count"] == 1 # case-103
    
    assert len(data["upcoming_followups"]) >= 1
    assert len(data["overdue_cases"]) == 1
    assert data["overdue_cases"][0]["id"] == "case-103"

def test_counsellor_dashboard_summary(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/dashboard/summary", headers=counselor_auth_headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["assigned_cases_count"] == 3
    assert summary["pending_cases_count"] == 1

def test_counsellor_upcoming_followups(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/dashboard/upcoming-followups", headers=counselor_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["case_id"] == "case-102"
    assert items[0]["status"] == "scheduled"

def test_counsellor_overdue_cases(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/dashboard/overdue-cases", headers=counselor_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == "case-103"
    assert items[0]["priority"] == "critical"

def test_get_counsellor_profile(client, counselor_auth_headers):
    resp = client.get("/api/v1/counsellor/profile", headers=counselor_auth_headers)
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["full_name"] == "Dr. Elena Rostova"
    assert "Academic Anxiety" in profile["specializations"]

def test_update_counsellor_profile(client, counselor_auth_headers):
    resp = client.patch("/api/v1/counsellor/profile", headers=counselor_auth_headers, json={
        "designation": "Principal Lead Student Counsellor",
        "phone": "+351-999-888-777",
        "specializations": ["Academic Anxiety", "Neurodiversity Guidance"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["designation"] == "Principal Lead Student Counsellor"
    assert data["phone"] == "+351-999-888-777"
    assert "Neurodiversity Guidance" in data["specializations"]

