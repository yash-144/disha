from datetime import datetime, timezone, timedelta

def test_full_counsellor_crm_lifecycle_e2e(client):
    """
    Complete end-to-end CRM lifecycle testing:
    1. Counsellor logs in.
    2. Dashboard loads with workload counts.
    3. Assigned students are displayed.
    4. Counsellor opens an assigned case.
    5. Counsellor reviews student information and observations.
    6. Counsellor accepts the case.
    7. Counsellor selects an intervention.
    8. Counsellor adds a case note.
    9. Counsellor schedules a follow-up.
    10. Counsellor completes the follow-up.
    11. Counsellor records the intervention outcome.
    12. Counsellor closes the case.
    13. Audit history displays the complete immutable hash-chained trail.
    """
    # 1. Counsellor logs in
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "counselor.disha@institution.edu",
        "password": "DishaCounsellor@2026"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    headers = {
        "Authorization": f"Bearer {token_data['access_token']}",
        "X-Campus-ID": token_data["campus_id"]
    }

    # 2. Dashboard loads
    dash_resp = client.get("/api/v1/counsellor/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["summary"]["assigned_cases_count"] >= 1
    assert dash_data["summary"]["pending_cases_count"] >= 1

    # 3. Assigned students displayed
    students_resp = client.get("/api/v1/counsellor/students", headers=headers)
    assert students_resp.status_code == 200
    students_data = students_resp.json()
    assert students_data["total"] >= 1
    target_student_id = "student-001"

    # 4. Counsellor opens an assigned case (case-101 for student-001)
    case_resp = client.get("/api/v1/cases/case-101", headers=headers)
    assert case_resp.status_code == 200
    case_detail = case_resp.json()
    assert case_detail["id"] == "case-101"
    assert case_detail["state"] == "assigned"
    version = case_detail["version"]

    # 5. Counsellor reviews student information and observations
    obs_resp = client.get(f"/api/v1/counsellor/students/{target_student_id}/observations", headers=headers)
    assert obs_resp.status_code == 200
    observations = obs_resp.json()
    assert len(observations) >= 2

    # 6. Counsellor accepts the case
    accept_resp = client.post("/api/v1/cases/case-101/accept", headers=headers, json={
        "expected_version": version,
        "acceptance_notes": "Student intake meeting scheduled."
    })
    assert accept_resp.status_code == 200
    accepted_case = accept_resp.json()
    assert accepted_case["state"] == "accepted"
    version = accepted_case["version"]

    # 7. Counsellor selects an intervention
    int_resp = client.post("/api/v1/cases/case-101/interventions", headers=headers, json={
        "intervention_key": "STUDY_SKILLS_WORKSHOP",
        "description": "Weekly study habits cohort"
    })
    assert int_resp.status_code == 201
    
    # Refresh version after intervention selection
    case_resp2 = client.get("/api/v1/cases/case-101", headers=headers)
    assert case_resp2.json()["state"] == "support_in_progress"
    version = case_resp2.json()["version"]

    # 8. Counsellor adds a case note
    note_resp = client.post("/api/v1/cases/case-101/notes", headers=headers, json={
        "content": "Intake completed. Student identified exam anxiety as root cause."
    })
    assert note_resp.status_code == 201

    # 9. Counsellor schedules a follow-up
    sched_time = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    fu_resp = client.post("/api/v1/cases/case-101/followups", headers=headers, json={
        "title": "Study Skills Week 1 Review",
        "scheduled_at": sched_time,
        "follow_up_type": "in_person_session",
        "notes": "Verify student attended first workshop."
    })
    assert fu_resp.status_code == 201
    follow_up_id = fu_resp.json()["id"]

    # 10. Counsellor completes the follow-up
    comp_resp = client.patch(f"/api/v1/followups/{follow_up_id}/complete", headers=headers, json={
        "completion_notes": "Student attended workshop and submitted schedule template.",
        "proof_data": "Workshop slip #9070"
    })
    assert comp_resp.status_code == 200
    assert comp_resp.json()["status"] == "completed"

    # 11. Counsellor records the intervention outcome
    outcome_resp = client.post("/api/v1/cases/case-101/outcome", headers=headers, json={
        "outcome_status": "helped",
        "outcome_notes": "Attendance normalized to 84% over past 3 weeks; passed midterm quiz."
    })
    assert outcome_resp.status_code == 200
    assert outcome_resp.json()["outcome_status"] == "helped"

    # Verify state moved to outcome_reviewed
    case_resp3 = client.get("/api/v1/cases/case-101", headers=headers)
    assert case_resp3.json()["state"] == "outcome_reviewed"
    version = case_resp3.json()["version"]

    # 12. Counsellor closes the case
    close_resp = client.post("/api/v1/cases/case-101/close", headers=headers, json={
        "expected_version": version,
        "reason_code": "STUDY_SKILLS_RESOLVED",
        "closing_notes": "Case successfully resolved. Student no longer at risk."
    })
    assert close_resp.status_code == 200
    closed_case = close_resp.json()
    assert closed_case["state"] == "closed"
    assert closed_case["closed_by"] is not None

    # 13. Audit history displays the complete workflow
    audit_resp = client.get("/api/v1/audit/logs", headers=headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["total_audit_events"] >= 6
    actions = [e["action"] for e in audit_data["events"]]
    assert "CASE_ACCEPTED" in actions
    assert "FOLLOWUP_SCHEDULED" in actions
    assert "FOLLOWUP_COMPLETED" in actions
    assert "OUTCOME_RECORDED" in actions
    assert "CASE_CLOSED" in actions

    # Verify hash-chain integrity
    for i in range(1, len(audit_data["events"])):
        prev_evt = audit_data["events"][i - 1]
        curr_evt = audit_data["events"][i]
        assert curr_evt["prev_hash"] == prev_evt["curr_hash"]

