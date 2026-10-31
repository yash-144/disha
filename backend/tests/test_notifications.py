def test_list_notifications(client, counselor_auth_headers):
    resp = client.get("/api/v1/notifications", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["id"] == "notif-001"
    assert data["items"][0]["title"] == "New Case Assigned: Ana Silva"

def test_filter_unread_notifications(client, counselor_auth_headers):
    resp = client.get("/api/v1/notifications?unread_only=true", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(not n["is_read"] for n in data["items"])

def test_mark_notification_read(client, counselor_auth_headers):
    resp = client.patch("/api/v1/notifications/notif-001/read", headers=counselor_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "notif-001"
    assert data["is_read"] is True

def test_cannot_read_another_users_notification(client, other_counselor_auth_headers):
    # Marcus Vance attempts to mark Elena's notification notif-001 as read
    resp = client.patch("/api/v1/notifications/notif-001/read", headers=other_counselor_auth_headers)
    assert resp.status_code == 403
    assert "another user" in resp.json()["error"]

