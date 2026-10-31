def test_optimistic_concurrency_case_acceptance(client, counselor_auth_headers):
    # Request 1 with expected_version=1 succeeds
    resp1 = client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={
        "expected_version": 1,
        "acceptance_notes": "First concurrent worker"
    })
    assert resp1.status_code == 200
    assert resp1.json()["version"] == 2

    # Request 2 with expected_version=1 receives 409 conflict
    resp2 = client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={
        "expected_version": 1,
        "acceptance_notes": "Stale concurrent worker"
    })
    assert resp2.status_code == 409
    assert "version" in resp2.json()["error"].lower()

def test_optimistic_concurrency_case_status_update(client, counselor_auth_headers):
    # Accept case-101 (moves to version 2)
    client.post("/api/v1/cases/case-101/accept", headers=counselor_auth_headers, json={"expected_version": 1})

    # Transition 1 succeeds with version 2
    resp1 = client.patch("/api/v1/cases/case-101/status", headers=counselor_auth_headers, json={
        "target_state": "contact_attempted",
        "expected_version": 2
    })
    assert resp1.status_code == 200
    assert resp1.json()["version"] == 3

    # Stale transition with version 2 gets 409
    resp2 = client.patch("/api/v1/cases/case-101/status", headers=counselor_auth_headers, json={
        "target_state": "support_in_progress",
        "expected_version": 2
    })
    assert resp2.status_code == 409

