def test_get_intervention_catalogue(client, counselor_auth_headers):
    resp = client.get("/api/v1/interventions/catalogue", headers=counselor_auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 4
    keys = [item["intervention_key"] for item in items]
    assert "ACADEMIC_PEER_TUTORING" in keys
    assert "COUNSELLOR_INTAKE_MEETING" in keys

def test_select_intervention_for_case(client, counselor_auth_headers):
    # First accept case-101
    client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={"expected_version": 1})

    resp = client.post("/api/v1/cases/case-101/interventions", headers=counselor_auth_headers, json={
        "intervention_key": "STUDY_SKILLS_WORKSHOP",
        "description": "Enrol in weekly 2-hour study skills cohort."
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["intervention_key"] == "STUDY_SKILLS_WORKSHOP"
    assert data["case_id"] == "case-101"

    # Verify case state progressed to support_in_progress
    detail_resp = client.get("/api/v1/cases/case-101", headers=counselor_auth_headers)
    assert detail_resp.json()["state"] == "support_in_progress"

def test_select_invalid_intervention_key_rejected(client, counselor_auth_headers):
    client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={"expected_version": 1})
    resp = client.post("/api/v1/cases/case-101/interventions", headers=counselor_auth_headers, json={
        "intervention_key": "NON_EXISTENT_INTERVENTION"
    })
    assert resp.status_code == 404

def test_record_intervention_outcome(client, counselor_auth_headers):
    resp = client.post("/api/v1/cases/case-102/outcome", headers=counselor_auth_headers, json={
        "outcome_status": "helped",
        "outcome_notes": "Student gained confidence and cleared backlog in calculus."
    })
    assert resp.status_code == 200
    outcome = resp.json()
    assert outcome["case_id"] == "case-102"
    assert outcome["outcome_status"] == "helped"
    assert "calculus" in outcome["outcome_notes"]

    # Verify state advanced to outcome_reviewed
    detail_resp = client.get("/api/v1/cases/case-102", headers=counselor_auth_headers)
    assert detail_resp.json()["state"] == "outcome_reviewed"
