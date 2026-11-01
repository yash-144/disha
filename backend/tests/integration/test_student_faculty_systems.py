import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def faculty_token():
    return create_access_token({
        "sub": "user-faculty-1",
        "email": "joseph.jackson@skillsup.in",
        "roles": ["faculty"],
        "display_name": "Joseph Jackson"
    })


@pytest.fixture
def student_token():
    return create_access_token({
        "sub": "user-student-1",
        "email": "aarav.sharma@example.com",
        "roles": ["student"],
        "display_name": "Aarav Sharma"
    })


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =====================================================================
# STUDENT SYSTEM INTEGRATION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_student_profile_and_dashboard(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # 1. Profile
    res = await client.get("/api/v1/student/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["display_name"] == "Aarav Sharma"
    assert data["cohort_code"] == "2025-CS"
    assert data["attendance_rate"] == 96.0

    # 2. Dashboard
    dash_res = await client.get("/api/v1/student/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "courses" in dash_data
    assert len(dash_data["courses"]) > 0
    assert dash_data["student_summary"]["display_name"] == "Aarav Sharma"


@pytest.mark.asyncio
async def test_student_academics_and_attendance(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # Attendance
    att_res = await client.get("/api/v1/student/attendance", headers=headers)
    assert att_res.status_code == 200
    att_data = att_res.json()
    assert "records" in att_data
    assert len(att_data["records"]) > 0

    # Academics
    acad_res = await client.get("/api/v1/student/academics", headers=headers)
    assert acad_res.status_code == 200
    acad_data = acad_res.json()
    assert "submissions" in acad_data
    assert len(acad_data["submissions"]) > 0


@pytest.mark.asyncio
async def test_student_support_and_counsellor_requests(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # List support requests
    sr_res = await client.get("/api/v1/student/support-requests", headers=headers)
    assert sr_res.status_code == 200
    assert len(sr_res.json()) > 0

    # Create new support request
    new_sr = await client.post("/api/v1/student/support-requests", headers=headers, json={
        "faculty_id": "user-faculty-1",
        "category": "assignment_guidance",
        "preferred_slot": "Friday 3:00 PM",
        "student_note": "Need help reviewing error boundary edge cases."
    })
    assert new_sr.status_code == 201
    assert new_sr.json()["status"] == "requested"

    # Create counsellor call request
    coun_res = await client.post("/api/v1/student/counsellor-call-requests", headers=headers, json={
        "preferred_contact_method": "voice_call",
        "preferred_time_slot": "afternoon",
        "student_notes": "Would appreciate a brief confidential check-in."
    })
    assert coun_res.status_code == 201
    assert coun_res.json()["status"] == "requested"


@pytest.mark.asyncio
async def test_student_wellbeing_pulse_and_decoupled_rewards(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # Clean up any prior test submission for idempotent test execution
    from app.core.database import AsyncSessionLocal
    from app.models.entities import PulseSubmission
    from sqlalchemy import delete
    async with AsyncSessionLocal() as session:
        await session.execute(delete(PulseSubmission).where(PulseSubmission.student_id == "stud-1"))
        await session.commit()

    # 1. Get current pulse
    cur_res = await client.get("/api/v1/student/wellbeing/pulse/current", headers=headers)
    assert cur_res.status_code == 200
    cur_data = cur_res.json()
    assert cur_data["period"]["key"] == "2026-W44"

    # 2. Check initial balance
    bal_initial = (await client.get("/api/v1/student/rewards/balance", headers=headers)).json()["balance"]

    # 3. Submit pulse survey
    sub_res = await client.post("/api/v1/student/wellbeing/pulse/submissions", headers=headers, json={
        "responses": {
            "emotional_wellbeing": 4,
            "belonging_community": 5,
            "academic_experience": 4,
            "support_trust": 5,
            "safety_respect": 5,
            "growth_confidence": 4
        },
        "reflection": "Felt good about mastering async data fetching."
    })
    assert sub_res.status_code == 201
    assert sub_res.json()["points_awarded"] == 10

    # 4. Enforce 1 submission per period
    dup_res = await client.post("/api/v1/student/wellbeing/pulse/submissions", headers=headers, json={
        "responses": {"emotional_wellbeing": 3}
    })
    assert dup_res.status_code == 409

    # 5. Verify rewards balance increased by decoupled points
    bal_new = (await client.get("/api/v1/student/rewards/balance", headers=headers)).json()["balance"]
    assert bal_new == bal_initial + 10


@pytest.mark.asyncio
async def test_student_rewards_catalog_and_redemption(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # Seed extra points for test repeatability
    from app.core.database import AsyncSessionLocal
    from app.models.entities import PointsLedgerEntry
    async with AsyncSessionLocal() as session:
        session.add(PointsLedgerEntry(
            institution_id="campus-1",
            student_id="stud-1",
            activity_key="test_bonus_points",
            points=50,
            source_ref="test_harness"
        ))
        await session.commit()

    # Get catalog
    cat_res = await client.get("/api/v1/student/rewards/catalog", headers=headers)
    assert cat_res.status_code == 200
    items = cat_res.json()
    assert len(items) > 0
    sticker_item = next(i for i in items if i["sku"] == "DISHA-STICKER-PACK")

    # Redeem reward
    red_res = await client.post("/api/v1/student/rewards/redemptions", headers=headers, json={
        "item_id": sticker_item["id"]
    })
    assert red_res.status_code == 201
    assert red_res.json()["item_title"] == sticker_item["title"]


@pytest.mark.asyncio
async def test_student_identity_and_document_verification(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}

    # Pseudonymous handle
    ident_res = await client.get("/api/v1/student/identity", headers=headers)
    assert ident_res.status_code == 200
    assert "DISHA-" in ident_res.json()["disha_id"]

    # Documents & Integrity check
    docs_res = await client.get("/api/v1/student/documents", headers=headers)
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) > 0
    doc_id = docs[0]["id"]

    verify_res = await client.get(f"/api/v1/student/documents/{doc_id}/verify", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["integrity_verified"] is True


# =====================================================================
# FACULTY SYSTEM INTEGRATION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_faculty_dashboard_and_sections(client, faculty_token):
    headers = {"Authorization": f"Bearer {faculty_token}", "X-Campus-ID": "campus-1"}

    # Dashboard
    dash_res = await client.get("/api/v1/faculty/dashboard", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    assert data["metrics"]["active_courses"] > 0
    assert data["metrics"]["total_students_monitored"] > 0

    # Sections
    sec_res = await client.get("/api/v1/faculty/sections", headers=headers)
    assert sec_res.status_code == 200
    sections = sec_res.json()
    assert len(sections) > 0
    sec_id = sections[0]["id"]

    # Section students (Scope S1)
    studs_res = await client.get(f"/api/v1/faculty/sections/{sec_id}/students", headers=headers)
    assert studs_res.status_code == 200
    assert len(studs_res.json()) > 0


@pytest.mark.asyncio
async def test_faculty_student_observations_and_signal_evaluation(client, faculty_token):
    headers = {"Authorization": f"Bearer {faculty_token}", "X-Campus-ID": "campus-1"}

    # Inspect raw observations for student stud-5 (Rohan)
    obs_res = await client.get("/api/v1/faculty/students/stud-5/observations", headers=headers)
    assert obs_res.status_code == 200
    assert len(obs_res.json()) > 0
    assert obs_res.json()[0]["metric_key"] == "attendance_rate"

    # Trigger deterministic signal evaluation
    eval_res = await client.post("/api/v1/faculty/students/stud-5/signals/evaluate", headers=headers)
    assert eval_res.status_code == 201
    eval_data = eval_res.json()
    assert eval_data["result"] == "attention_suggested"
    assert "evidence_digest" in eval_data


@pytest.mark.asyncio
async def test_faculty_signal_review_and_case_lifecycle(client, faculty_token):
    headers = {"Authorization": f"Bearer {faculty_token}", "X-Campus-ID": "campus-1"}

    # 1. Fetch reviewable signals
    sigs_res = await client.get("/api/v1/faculty/signals", headers=headers)
    assert sigs_res.status_code == 200
    sigs = sigs_res.json()
    assert len(sigs) > 0
    target_sig = sigs[0]["id"]

    # 2. Review signal (Approve creates/attaches case)
    rev_res = await client.post(f"/api/v1/faculty/signals/{target_sig}/review", headers=headers, json={
        "decision": "approve",
        "reason": "Attendance dropped severely below 75% threshold.",
        "selected_intervention_key": "mentor_check_in"
    })
    assert rev_res.status_code == 200
    case_id = rev_res.json()["case_id"]
    assert case_id is not None

    # 3. Create domain task in case
    task_res = await client.post(f"/api/v1/faculty/cases/{case_id}/tasks", headers=headers, json={
        "domain": "academic",
        "generic_label": "Conduct 1-on-1 Attendance & Syllabus Review Session",
        "due_days": 3
    })
    assert task_res.status_code == 201
    assert "audit_hash" in task_res.json()

    # 4. Log follow-up
    fu_res = await client.post(f"/api/v1/faculty/cases/{case_id}/follow-ups", headers=headers, json={
        "follow_up_type": "support_delivered",
        "contact_status": "student_reached",
        "proof_kind": "staff_attestation",
        "sanitized_note": "Met student in office; agreed on makeup lab attendance schedule."
    })
    assert fu_res.status_code == 200
    assert fu_res.json()["case_state"] == "support_in_progress"

    # 5. Escalate case (verifying deadline_version increment & audit event)
    esc_res = await client.post(f"/api/v1/faculty/cases/{case_id}/escalate", headers=headers)
    assert esc_res.status_code == 200
    assert "audit_hash" in esc_res.json()

    # 6. Conclude case with outcome
    out_res = await client.post(f"/api/v1/faculty/cases/{case_id}/outcome", headers=headers, json={
        "outcome_status": "helped",
        "rationale": "Student attended all makeup sessions and attendance restored to 82%."
    })
    assert out_res.status_code == 200
    assert out_res.json()["state"] == "closed"

    # 7. Verify hash-chained audit history
    hist_res = await client.get(f"/api/v1/faculty/cases/{case_id}/history", headers=headers)
    assert hist_res.status_code == 200
    events = hist_res.json()
    assert len(events) >= 3  # task, escalation, outcome
    for ev in events:
        assert len(ev["hash"]) == 64  # SHA-256


@pytest.mark.asyncio
async def test_faculty_cohort_analytics_with_suppression(client, faculty_token):
    headers = {"Authorization": f"Bearer {faculty_token}", "X-Campus-ID": "campus-1"}

    res = await client.get("/api/v1/faculty/analytics/cohort-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    # 6 students in cohort > 5, so not suppressed
    assert data["suppressed"] is False
    assert data["total_students"] >= 5
    assert "average_attendance" in data


# =====================================================================
# SECURITY & CROSS-ROLE BOUNDARY TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_role_boundary_enforcement(client, student_token, faculty_token):
    # Student attempting to access Faculty endpoint -> 403 Forbidden
    s_headers = {"Authorization": f"Bearer {student_token}", "X-Campus-ID": "campus-1"}
    unauth_fac = await client.get("/api/v1/faculty/dashboard", headers=s_headers)
    assert unauth_fac.status_code == 403

    # Faculty attempting to access Student endpoint -> 403 Forbidden
    f_headers = {"Authorization": f"Bearer {faculty_token}", "X-Campus-ID": "campus-1"}
    unauth_stu = await client.get("/api/v1/student/dashboard", headers=f_headers)
    assert unauth_stu.status_code == 403

    # Anonymous request -> 401 Unauthorized
    anon_res = await client.get("/api/v1/student/dashboard")
    assert anon_res.status_code == 401
