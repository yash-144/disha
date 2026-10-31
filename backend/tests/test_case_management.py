def test_list_assigned_cases(client, counselor_auth_headers):
    resp = client.get("/api/v1/cases", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    case_ids = [c["id"] for c in data["items"]]
    assert "case-101" in case_ids

def test_view_case_details(client, counselor_auth_headers):
    resp = client.get("/api/v1/cases/case-101", headers=counselor_auth_headers)
    assert resp.status_code == 200
    case = resp.json()
    assert case["id"] == "case-101"
    assert case["student"]["display_name"] == "Ana Silva"
    assert case["state"] == "assigned"
    assert len(case["observations"]) >= 2
    assert len(case["timeline"]) >= 1

def test_accept_assigned_case(client, counselor_auth_headers):
    # case-101 has version 1 and is in 'assigned' state
    resp = client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={
        "expected_version": 1,
        "acceptance_notes": "Intake assessment scheduled with student Ana."
    })
    assert resp.status_code == 200
    case = resp.json()
    assert case["state"] == "accepted"
    assert case["accepted_at"] is not None
    assert case["version"] == 2

    # Verify timeline event was added
    timeline_resp = client.get("/api/v1/cases/case-101/timeline", headers=counselor_auth_headers)
    assert timeline_resp.status_code == 200
    events = timeline_resp.json()
    event_types = [e["event_type"] for e in events]
    assert "CASE_ACCEPTED" in event_types

def test_accept_case_invalid_state(client, counselor_auth_headers):
    # case-102 is in 'support_in_progress', not 'assigned'
    resp = client.post("/api/v1/cases/case-102/accept", headers=counselor_auth_headers, json={
        "expected_version": 3
    })
    assert resp.status_code == 422
    assert "must be in 'assigned' state" in resp.json()["error"]

def test_update_case_status_valid_transition(client, counselor_auth_headers):
    # First accept case-101
    client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={"expected_version": 1})
    
    # Transition from 'accepted' to 'contact_attempted'
    resp = client.patch("/api/v1/cases/case-101/status", headers=counselor_auth_headers, json={
        "target_state": "contact_attempted",
        "expected_version": 2,
        "reason_code": "OUTREACH_EMAIL_SENT",
        "notes": "Sent introductory guidance email to student."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "contact_attempted"
    assert data["version"] == 3

def test_update_case_status_invalid_transition_rejected(client, counselor_auth_headers):
    # case-101 is 'assigned'; cannot jump directly to 'closed'
    resp = client.patch("/api/v1/cases/case-101/status", headers=counselor_auth_headers, json={
        "target_state": "closed",
        "expected_version": 1
    })
    assert resp.status_code == 422
    assert "Invalid state transition" in resp.json()["error"]

def test_add_and_list_case_notes(client, counselor_auth_headers):
    resp = client.post("/api/v1/cases/case-101/notes", headers=counselor_auth_headers, json={
        "content": "Student reported initial difficulty adjusting to commute."
    })
    assert resp.status_code == 201
    note = resp.json()
    assert note["author_name"] == "Dr. Elena Rostova"
    assert "difficulty adjusting" in note["content"]

    # List notes
    list_resp = client.get("/api/v1/cases/case-101/notes", headers=counselor_auth_headers)
    assert list_resp.status_code == 200
    notes = list_resp.json()
    assert len(notes) == 1
    assert notes[0]["id"] == note["id"]

def test_close_case(client, counselor_auth_headers):
    # Advance case-102 (support_in_progress) -> outcome_reviewed -> closed
    # First record outcome on case-102
    client.post("/api/v1/cases/case-102/outcome", headers=counselor_auth_headers, json={
        "outcome_status": "helped",
        "outcome_notes": "Student attended study skills workshops and improved attendance."
    })
    
    # Check case-102 details for version
    detail_resp = client.get("/api/v1/cases/case-102", headers=counselor_auth_headers)
    curr_version = detail_resp.json()["version"]

    close_resp = client.post("/api/v1/cases/case-102/close", headers=counselor_auth_headers, json={
        "expected_version": curr_version,
        "reason_code": "ACADEMIC_RECOVERY_ACHIEVED",
        "closing_notes": "Goal met. Student attendance stabilized at 88%."
    })
    assert close_resp.status_code == 200
    closed_case = close_resp.json()
    assert closed_case["state"] == "closed"
    assert closed_case["closed_at"] is not None
    assert closed_case["closed_by"] == "user-counselor-01"
