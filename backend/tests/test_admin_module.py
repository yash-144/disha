import pytest
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, r"d:\Programming\hackathon2026\disha\backend")
from app.main import app
from app.core.database import db
from app.core.security import create_access_token

@pytest.fixture(autouse=True)
def reset_database():
    """Reset the database to clean pre-seeded state before each test."""
    db.reset()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_headers():
    token = create_access_token({
        "sub": "user-admin-01",
        "email": "admin.disha@institution.edu",
        "roles": ["institution_admin"],
        "campus_id": "campus-ipp-01",
        "full_name": "Dr. Sarah Jenkins"
    })
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": "campus-ipp-01"
    }

@pytest.fixture
def platform_admin_headers():
    token = create_access_token({
        "sub": "user-platform-admin-01",
        "email": "platform.admin@disha.edu",
        "roles": ["platform_admin"],
        "campus_id": "campus-ipp-01",
        "full_name": "Alexander Sterling"
    })
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": "campus-ipp-01"
    }

@pytest.fixture
def counsellor_headers():
    token = create_access_token({
        "sub": "user-counselor-01",
        "email": "counselor.disha@institution.edu",
        "roles": ["counsellor"],
        "campus_id": "campus-ipp-01",
        "full_name": "Dr. Elena Rostova"
    })
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": "campus-ipp-01"
    }

@pytest.fixture
def other_campus_headers():
    token = create_access_token({
        "sub": "user-admin-foreign",
        "email": "foreign.admin@other.edu",
        "roles": ["institution_admin"],
        "campus_id": "campus-foreign-99",
        "full_name": "Foreign Admin"
    })
    return {
        "Authorization": f"Bearer {token}",
        "X-Campus-ID": "campus-foreign-99"
    }


# ==========================================
# 1. UNIT & SERVICE INTEGRATION TESTS
# ==========================================

def test_admin_dashboard_summary(client, admin_headers):
    """A01-A10: Verify dashboard aggregates real data and statistics."""
    res = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 3
    assert data["total_faculty"] == 1
    assert data["total_counsellors"] == 2
    assert data["total_active_cases"] == 3
    assert data["overdue_cases"] == 1 # case-103
    assert len(data["counsellor_workload"]) >= 1
    assert len(data["recent_activities"]) >= 1

def test_counsellor_workload_endpoint(client, admin_headers):
    """A08: Test counsellor workload distribution overview."""
    res = client.get("/api/v1/admin/dashboard/counsellor-workload", headers=admin_headers)
    assert res.status_code == 200
    workload = res.json()
    assert isinstance(workload, list)
    elena = next((c for c in workload if c["user_id"] == "user-counselor-01"), None)
    assert elena is not None
    assert elena["active_cases"] >= 2

def test_user_filtering_and_search(client, admin_headers):
    """A11-A13: Search and filter users by role and text."""
    # Filter by role
    res = client.get("/api/v1/admin/users?role=counsellor", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert all("counsellor" in u["roles"] for u in data["items"])

    # Search by name
    res_search = client.get("/api/v1/admin/users?search=Elena", headers=admin_headers)
    assert res_search.status_code == 200
    items = res_search.json()["items"]
    assert len(items) == 1
    assert items[0]["full_name"] == "Dr. Elena Rostova"

def test_invite_staff_and_duplicate_prevention(client, admin_headers):
    """A14-A16: Invite staff and check duplicate prevention."""
    payload = {
        "email": "new.faculty@institution.edu",
        "full_name": "Prof. Alan Turing",
        "role": "faculty",
        "department": "Computer Science"
    }
    res = client.post("/api/v1/admin/invitations", json=payload, headers=admin_headers)
    assert res.status_code == 201
    inv_data = res.json()
    assert inv_data["email"] == "new.faculty@institution.edu"
    assert inv_data["status"] == "PENDING"

    # Attempt duplicate invitation should fail with 400
    res_dup = client.post("/api/v1/admin/invitations", json=payload, headers=admin_headers)
    assert res_dup.status_code == 400

def test_membership_update(client, admin_headers):
    """A17-A19: Deactivate membership and update roles."""
    target_user = "user-faculty-01"
    patch_payload = {
        "is_active": False,
        "department": "Applied Sciences"
    }
    res = client.patch(f"/api/v1/admin/memberships/{target_user}", json=patch_payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_active"] is False
    assert data["department"] == "Applied Sciences"

def test_campus_management(client, admin_headers):
    """A21-A25: View and update campus details and config."""
    res = client.get("/api/v1/admin/campus", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["id"] == "campus-ipp-01"

    update_payload = {
        "name": "Polytechnic Institute of Portalegre - Main Campus",
        "configuration": {"sla_acceptance_days": 2}
    }
    patch_res = client.patch("/api/v1/admin/campus", json=update_payload, headers=admin_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Polytechnic Institute of Portalegre - Main Campus"
    assert patch_res.json()["configuration"]["sla_acceptance_days"] == 2

def test_case_supervision_and_overdue_tracking(client, admin_headers):
    """A26-A30: Case listing, overdue filtering, and details."""
    res_cases = client.get("/api/v1/admin/cases", headers=admin_headers)
    assert res_cases.status_code == 200
    assert len(res_cases.json()) == 3

    res_overdue = client.get("/api/v1/admin/cases/overdue", headers=admin_headers)
    assert res_overdue.status_code == 200
    overdue_list = res_overdue.json()
    assert len(overdue_list) == 1
    assert overdue_list[0]["id"] == "case-103"
    assert overdue_list[0]["is_overdue"] is True

    # Case detail
    res_detail = client.get("/api/v1/admin/cases/case-101", headers=admin_headers)
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["student_name"] == "Ana Silva"
    assert "interventions" in detail
    assert "timeline_events" in detail

def test_case_reassignment_with_audit_and_notification(client, admin_headers):
    """A31: Supervisor case reassignment with optimistic locking, audit and notification."""
    case_id = "case-101"
    initial_case = db.cases[case_id]
    expected_v = initial_case["version"]

    reassign_payload = {
        "new_counsellor_user_id": "user-counselor-02",
        "reassignment_reason": "Balancing departmental caseloads",
        "expected_version": expected_v
    }
    res = client.post(f"/api/v1/admin/cases/{case_id}/reassign", json=reassign_payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["primary_owner_user_id"] == "user-counselor-02"
    assert data["version"] == expected_v + 1

    # Verify notification was generated for new counsellor
    notif = next((n for n in db.notifications.values() if n["user_id"] == "user-counselor-02"), None)
    assert notif is not None
    assert "Case Transferred to You" in notif["title"]

    # Test Optimistic Lock conflict on stale version
    res_conflict = client.post(f"/api/v1/admin/cases/{case_id}/reassign", json=reassign_payload, headers=admin_headers)
    assert res_conflict.status_code == 409

def test_data_import_monitoring(client, admin_headers):
    """A34-A37: View data import logs and validation errors."""
    res = client.get("/api/v1/admin/imports", headers=admin_headers)
    assert res.status_code == 200
    imports = res.json()
    assert len(imports) >= 2

    # View error log for import-002
    res_err = client.get("/api/v1/admin/imports/import-002/errors", headers=admin_headers)
    assert res_err.status_code == 200
    err_data = res_err.json()
    assert len(err_data["errors"]) == 3

def test_analytics_and_audit(client, admin_headers):
    """A38-A48: Operational statistics and immutable audit logging."""
    res_analytics = client.get("/api/v1/admin/analytics/overview", headers=admin_headers)
    assert res_analytics.status_code == 200
    an_data = res_analytics.json()
    assert "case_volume_by_priority" in an_data
    assert "resolution_rate_pct" in an_data

    # Audit events
    res_audit = client.get("/api/v1/admin/audit", headers=admin_headers)
    assert res_audit.status_code == 200
    events = res_audit.json()
    assert len(events) >= 1
    assert all("curr_hash" in e for e in events)

def test_admin_profile_and_password(client, admin_headers):
    """A49-A51: Administrator profile inspection and password update."""
    res = client.get("/api/v1/admin/profile", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["full_name"] == "Dr. Sarah Jenkins"

    # Update profile
    patch_res = client.patch("/api/v1/admin/profile", json={"department": "Central Student Deanery"}, headers=admin_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["department"] == "Central Student Deanery"

    # Password change
    pw_payload = {
        "current_password": "DishaAdmin@2026",
        "new_password": "NewSecureAdminPassword@2026"
    }
    pw_res = client.post("/api/v1/admin/profile/change-password", json=pw_payload, headers=admin_headers)
    assert pw_res.status_code == 200


# ==========================================
# 2. AUTHORIZATION & TENANCY TESTS
# ==========================================

def test_counsellor_forbidden_from_admin_endpoints(client, counsellor_headers):
    """Verify non-admin role (counsellor) is rejected with 403 Forbidden."""
    res = client.get("/api/v1/admin/dashboard", headers=counsellor_headers)
    assert res.status_code == 403

    res_users = client.get("/api/v1/admin/users", headers=counsellor_headers)
    assert res_users.status_code == 403

def test_anonymous_forbidden(client):
    """Verify unauthenticated request is rejected with 401 Unauthorized."""
    res = client.get("/api/v1/admin/dashboard")
    assert res.status_code == 401

def test_cross_campus_isolation(client, other_campus_headers):
    """Verify campus isolation: admin from other campus cannot access or see campus-ipp-01 records."""
    res = client.get("/api/v1/admin/dashboard", headers=other_campus_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 0
    assert data["total_active_cases"] == 0

    # Cross-campus case detail access fails with 404
    res_case = client.get("/api/v1/admin/cases/case-101", headers=other_campus_headers)
    assert res_case.status_code == 404

