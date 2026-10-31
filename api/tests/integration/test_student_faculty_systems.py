import unittest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.core.permissions import Role
from app.shared.utils import utc_now
from app.modules.campus.models import CampusEntity
from app.modules.identity.models import User, Membership
from app.modules.roster.models import Student, Observation
from app.modules.faculty.models import (
    FacultyProfile,
    Course,
    CourseSection,
    CourseEnrollment,
    StudentAttendanceRecord,
    Assessment,
    AssessmentSubmission,
)
from app.modules.cases.models import Signal, Case, CaseNote


class TestStudentFacultySystems(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed fixtures
        async with self.async_session() as session:
            now = utc_now()
            pwd = get_password_hash("password123")

            # 1. Campus
            session.add(CampusEntity(id="campus-1", created_at=now))
            session.add(CampusEntity(id="campus-2", created_at=now))

            # 2. Users
            self.fac_user = User(
                id="user-faculty-1",
                email="joseph.jackson@skillsup.in",
                hashed_password=pwd,
                full_name="Joseph Jackson",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(self.fac_user)

            self.stu_user = User(
                id="user-student-1",
                email="aarav.sharma@example.com",
                hashed_password=pwd,
                full_name="Aarav Sharma",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(self.stu_user)

            self.coun_user = User(
                id="user-counsellor-1",
                email="counsellor@skillsup.in",
                hashed_password=pwd,
                full_name="Dr. Anita Desai",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(self.coun_user)

            # 3. Memberships
            session.add(Membership(
                id="mem-fac-1",
                user_id="user-faculty-1",
                campus_id="campus-1",
                role=Role.FACULTY.value,
                department="Computer Science",
                is_active=True,
                created_at=now,
            ))
            session.add(Membership(
                id="mem-stu-1",
                user_id="user-student-1",
                campus_id="campus-1",
                role=Role.STUDENT.value,
                department="Computer Science",
                is_active=True,
                created_at=now,
            ))
            session.add(Membership(
                id="mem-coun-1",
                user_id="user-counsellor-1",
                campus_id="campus-1",
                role=Role.COUNSELLOR.value,
                department="Welfare",
                is_active=True,
                created_at=now,
            ))

            # 4. Students
            self.stu1 = Student(
                id="stud-1",
                campus_id="campus-1",
                user_id="user-student-1",
                student_uid="STU-1001",
                full_name="Aarav Sharma",
                email="aarav.sharma@example.com",
                department="Computer Science",
                cohort_code="2025-CS",
                attendance_rate=96.0,
                quiz_score_avg=88.0,
                enrollment_status="active",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(self.stu1)

            self.stu5 = Student(
                id="stud-5",
                campus_id="campus-1",
                user_id=None,
                student_uid="STU-1005",
                full_name="Rohan Deshmukh",
                email="rohan.d@example.com",
                department="Computer Science",
                cohort_code="2025-CS",
                attendance_rate=71.0,
                quiz_score_avg=64.0,
                enrollment_status="active",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(self.stu5)

            # 5. Course & Section
            self.course = Course(
                id="course-1",
                campus_id="campus-1",
                code="CS402",
                title="Full-Stack Web Development",
                category="Computer Science",
                credits=4,
                semester="Fall 2025",
                primary_faculty_id="user-faculty-1",
                created_at=now,
            )
            session.add(self.course)

            self.sec = CourseSection(
                id="sec-1",
                campus_id="campus-1",
                course_id="course-1",
                faculty_id="user-faculty-1",
                section_code="CS402-A",
                name="CS402 Section A",
                term="July - Dec 2025",
                access_code="acc-sec-1",
                subject="Computer Science",
                color="bg-blue-600",
                created_at=now,
            )
            session.add(self.sec)

            # 6. Enrollments
            session.add(CourseEnrollment(
                id="enr-1",
                campus_id="campus-1",
                section_id="sec-1",
                student_id="stud-1",
                status="enrolled",
                enrolled_at=now,
            ))
            session.add(CourseEnrollment(
                id="enr-5",
                campus_id="campus-1",
                section_id="sec-1",
                student_id="stud-5",
                status="enrolled",
                enrolled_at=now,
            ))

            # 7. Attendance Record
            session.add(StudentAttendanceRecord(
                id="att-1",
                campus_id="campus-1",
                section_id="sec-1",
                student_id="stud-1",
                date="2026-11-01",
                status="Present",
                recorded_by="user-faculty-1",
                recorded_at=now,
            ))

            # 8. Assessment & Submission
            self.ass = Assessment(
                id="ass-1",
                campus_id="campus-1",
                section_id="sec-1",
                title="Mid-term React Quiz",
                assessment_type="quiz",
                total_marks=100.0,
                clo_code="CLO-1",
                created_by="user-faculty-1",
                created_at=now,
            )
            session.add(self.ass)

            session.add(AssessmentSubmission(
                id="sub-1",
                campus_id="campus-1",
                assessment_id="ass-1",
                student_id="stud-1",
                score=92.0,
                feedback="Great work on hooks",
                graded_by="user-faculty-1",
                submitted_at=now,
            ))

            # 9. Observation for Rohan (stud-5)
            session.add(Observation(
                id="obs-5",
                student_id="stud-5",
                campus_id="campus-1",
                domain="attendance",
                source="SIS-LMS",
                data="Attendance dropped to 71%",
                observed_at=now,
                created_at=now,
            ))

            await session.commit()

        async def override_get_db():
            async with self.async_session() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        self.faculty_token = create_access_token({
            "sub": "user-faculty-1",
            "email": "joseph.jackson@skillsup.in",
            "campus_id": "campus-1",
            "role": "faculty",
        })
        self.student_token = create_access_token({
            "sub": "user-student-1",
            "email": "aarav.sharma@example.com",
            "campus_id": "campus-1",
            "role": "student",
        })

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        await self.engine.dispose()

    # =====================================================================
    # STUDENT SYSTEM INTEGRATION TESTS
    # =====================================================================

    def test_student_profile_and_dashboard(self):
        headers = {"Authorization": f"Bearer {self.student_token}", "X-Campus-ID": "campus-1"}

        # 1. Profile
        res = self.client.get("/api/v1/student/profile", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["display_name"], "Aarav Sharma")
        self.assertEqual(data["cohort_code"], "2025-CS")
        self.assertEqual(data["attendance_rate"], 96.0)

        # 2. Dashboard
        dash_res = self.client.get("/api/v1/student/dashboard", headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.json()
        self.assertIn("courses", dash_data)
        self.assertGreater(len(dash_data["courses"]), 0)
        self.assertEqual(dash_data["student_summary"]["display_name"], "Aarav Sharma")

    def test_student_academics_and_attendance(self):
        headers = {"Authorization": f"Bearer {self.student_token}", "X-Campus-ID": "campus-1"}

        # Attendance
        att_res = self.client.get("/api/v1/student/attendance", headers=headers)
        self.assertEqual(att_res.status_code, 200)
        att_data = att_res.json()
        self.assertIn("records", att_data)
        self.assertGreater(len(att_data["records"]), 0)

        # Academics
        acad_res = self.client.get("/api/v1/student/academics", headers=headers)
        self.assertEqual(acad_res.status_code, 200)
        acad_data = acad_res.json()
        self.assertIn("submissions", acad_data)
        self.assertGreater(len(acad_data["submissions"]), 0)

    def test_student_support_requests(self):
        headers = {"Authorization": f"Bearer {self.student_token}", "X-Campus-ID": "campus-1"}

        # List support requests
        sr_res = self.client.get("/api/v1/student/support-requests", headers=headers)
        self.assertEqual(sr_res.status_code, 200)
        self.assertIsInstance(sr_res.json(), list)

        # Create new support request
        new_sr = self.client.post("/api/v1/student/support-requests", headers=headers, json={
            "faculty_id": "user-faculty-1",
            "category": "assignment_guidance",
            "preferred_slot": "Friday 3:00 PM",
            "student_note": "Need help reviewing error boundary edge cases.",
            "course_id": "course-1",
        })
        self.assertEqual(new_sr.status_code, 201)
        self.assertEqual(new_sr.json()["status"], "requested")

    # =====================================================================
    # FACULTY SYSTEM INTEGRATION TESTS
    # =====================================================================

    def test_faculty_dashboard_and_sections(self):
        headers = {"Authorization": f"Bearer {self.faculty_token}", "X-Campus-ID": "campus-1"}

        # Dashboard
        dash_res = self.client.get("/api/v1/faculty/dashboard", headers=headers)
        self.assertEqual(dash_res.status_code, 200)
        data = dash_res.json()
        self.assertGreater(data["metrics"]["active_courses"], 0)
        self.assertGreater(data["metrics"]["total_students_monitored"], 0)

        # Sections
        sec_res = self.client.get("/api/v1/faculty/sections", headers=headers)
        self.assertEqual(sec_res.status_code, 200)
        sections = sec_res.json()
        self.assertGreater(len(sections), 0)
        sec_id = sections[0]["id"]

        # Section students
        studs_res = self.client.get(f"/api/v1/faculty/sections/{sec_id}/students", headers=headers)
        self.assertEqual(studs_res.status_code, 200)
        self.assertGreater(len(studs_res.json()), 0)

    def test_faculty_student_observations_and_signal_evaluation(self):
        headers = {"Authorization": f"Bearer {self.faculty_token}", "X-Campus-ID": "campus-1"}

        # Inspect raw observations for student stud-5 (Rohan)
        obs_res = self.client.get("/api/v1/faculty/students/stud-5/observations", headers=headers)
        self.assertEqual(obs_res.status_code, 200)
        self.assertGreater(len(obs_res.json()), 0)
        self.assertEqual(obs_res.json()[0]["metric_key"], "attendance_rate")

        # Trigger deterministic signal evaluation
        eval_res = self.client.post("/api/v1/faculty/students/stud-5/signals/evaluate", headers=headers)
        self.assertEqual(eval_res.status_code, 201)
        eval_data = eval_res.json()
        self.assertEqual(eval_data["result"], "attention_suggested")
        self.assertIn("evidence_digest", eval_data)

    def test_faculty_signal_review_and_case_lifecycle(self):
        headers = {"Authorization": f"Bearer {self.faculty_token}", "X-Campus-ID": "campus-1"}

        # Trigger evaluation first to have a signal
        eval_res = self.client.post("/api/v1/faculty/students/stud-5/signals/evaluate", headers=headers)
        self.assertEqual(eval_res.status_code, 201)

        # 1. Fetch reviewable signals
        sigs_res = self.client.get("/api/v1/faculty/signals", headers=headers)
        self.assertEqual(sigs_res.status_code, 200)
        sigs = sigs_res.json()
        self.assertGreater(len(sigs), 0)
        target_sig = sigs[0]["id"]

        # 2. Review signal (Approve creates/attaches case)
        rev_res = self.client.post(f"/api/v1/faculty/signals/{target_sig}/review", headers=headers, json={
            "decision": "approve",
            "reason": "Attendance dropped severely below 75% threshold.",
            "selected_intervention_key": "mentor_check_in",
        })
        self.assertEqual(rev_res.status_code, 200)
        case_id = rev_res.json()["case_id"]
        self.assertIsNotNone(case_id)

        # 3. Create domain task in case
        task_res = self.client.post(f"/api/v1/faculty/cases/{case_id}/tasks", headers=headers, json={
            "domain": "academic",
            "generic_label": "Conduct 1-on-1 Attendance & Syllabus Review Session",
            "due_days": 3,
        })
        self.assertEqual(task_res.status_code, 201)
        self.assertIn("audit_hash", task_res.json())

        # 4. Log follow-up
        fu_res = self.client.post(f"/api/v1/faculty/cases/{case_id}/follow-ups", headers=headers, json={
            "follow_up_type": "support_delivered",
            "contact_status": "student_reached",
            "proof_kind": "staff_attestation",
            "sanitized_note": "Met student in office; agreed on makeup lab attendance schedule.",
        })
        self.assertEqual(fu_res.status_code, 200)
        self.assertEqual(fu_res.json()["case_state"], "support_in_progress")

        # 5. Escalate case
        esc_res = self.client.post(f"/api/v1/faculty/cases/{case_id}/escalate", headers=headers)
        self.assertEqual(esc_res.status_code, 200)
        self.assertIn("audit_hash", esc_res.json())

        # 6. Conclude case with outcome
        out_res = self.client.post(f"/api/v1/faculty/cases/{case_id}/outcome", headers=headers, json={
            "outcome_status": "helped",
            "rationale": "Student attended all makeup sessions and attendance restored to 82%.",
        })
        self.assertEqual(out_res.status_code, 200)
        self.assertEqual(out_res.json()["state"], "closed")

        # 7. Verify audit history
        hist_res = self.client.get(f"/api/v1/faculty/cases/{case_id}/history", headers=headers)
        self.assertEqual(hist_res.status_code, 200)
        events = hist_res.json()
        self.assertGreaterEqual(len(events), 3)

    # =====================================================================
    # SECURITY & CROSS-ROLE BOUNDARY TESTS
    # =====================================================================

    def test_role_boundary_enforcement(self):
        # Student attempting to access Faculty endpoint -> 403 Forbidden
        s_headers = {"Authorization": f"Bearer {self.student_token}", "X-Campus-ID": "campus-1"}
        unauth_fac = self.client.get("/api/v1/faculty/dashboard", headers=s_headers)
        self.assertEqual(unauth_fac.status_code, 403)

        # Faculty attempting to access Student endpoint -> 403 Forbidden
        f_headers = {"Authorization": f"Bearer {self.faculty_token}", "X-Campus-ID": "campus-1"}
        unauth_stu = self.client.get("/api/v1/student/dashboard", headers=f_headers)
        self.assertEqual(unauth_stu.status_code, 403)

        # Anonymous request -> 401 Unauthorized
        anon_res = self.client.get("/api/v1/student/dashboard")
        self.assertEqual(anon_res.status_code, 401)

    def test_faculty_section_and_student_isolation(self):
        headers = {"Authorization": f"Bearer {self.faculty_token}", "X-Campus-ID": "campus-1"}

        # Attempting to access non-existent or unassigned section -> 403 Forbidden
        unauth_sec = self.client.get("/api/v1/faculty/sections/unassigned-sec-999/students", headers=headers)
        self.assertEqual(unauth_sec.status_code, 403)

        # Attempting to access student not enrolled in faculty sections -> 403 Forbidden
        unauth_stu = self.client.get("/api/v1/faculty/students/stud-not-enrolled/attendance", headers=headers)
        self.assertEqual(unauth_stu.status_code, 403)


if __name__ == "__main__":
    unittest.main()
