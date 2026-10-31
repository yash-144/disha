from datetime import datetime, timezone, timedelta

def test_schedule_followup(client, counselor_auth_headers):
    sched_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    resp = client.post("/api/v1/cases/case-101/followups", headers=counselor_auth_headers, json={
        "title": "Post-Intake Reflection Meeting",
        "scheduled_at": sched_time,
        "follow_up_type": "in_person_session",
        "notes": "Review student time log."
    })
    assert resp.status_code == 201
    fu = resp.json()
    assert fu["case_id"] == "case-101"
    assert fu["title"] == "Post-Intake Reflection Meeting"
    assert fu["status"] == "scheduled"

def test_list_case_followups(client, counselor_auth_headers):
    resp = client.get("/api/v1/cases/case-102/followups", headers=counselor_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["id"] == "fu-201"

def test_complete_followup_idempotent(client, counselor_auth_headers):
    # Complete pre-seeded follow-up fu-201
    resp1 = client.patch("/api/v1/followups/fu-201/complete", headers=counselor_auth_headers, json={
        "completion_notes": "Student attended and confirmed tutoring session.",
        "proof_data": "Signed slip verified by peer coordinator."
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "completed"
    assert data1["completed_at"] is not None
    assert data1["completed_by"] == "user-counselor-01"

    # Idempotent second call should succeed without re-updating
    resp2 = client.patch("/api/v1/followups/fu-201/complete", headers=counselor_auth_headers, json={
        "completion_notes": "Duplicate call"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "completed"
    assert data2["completed_at"] == data1["completed_at"]

def test_add_followup_note(client, counselor_auth_headers):
    resp = client.post("/api/v1/followups/fu-201/notes", headers=counselor_auth_headers, json={
        "content": "Student sent email stating 10 minute delay due to bus strike."
    })
    assert resp.status_code == 200
    fu = resp.json()
    assert "bus strike" in fu["notes"]

def test_counsellor_followup_history(client, counselor_auth_headers):
    # Complete fu-201
    client.patch("/api/v1/followups/fu-201/complete", headers=counselor_auth_headers)

    resp = client.get("/api/v1/counsellor/followups/history", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
