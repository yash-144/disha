import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.entities import (
    Institution,
    UserProfile,
    InstitutionMembership,
    Student,
    StudentAccountLink,
    Course,
    CourseSection,
    CourseEnrollment,
    StudentAttendanceRecord,
    Assessment,
    AssessmentSubmission,
    SupportRequest,
    Signal,
    Case,
    FollowUp,
    Notification,
    utc_now,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_data():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select
        res = await session.execute(select(Institution).limit(1))
        if res.scalar_one_or_none():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding initial DISHA data...")

        # 1. Institution
        inst = Institution(
            id="campus-1",
            name="DISHA National Institute of Technology",
            code="DNIT-MAIN",
            status="active"
        )
        session.add(inst)

        # 2. Users
        pwd_hash = get_password_hash("password123")

        faculty_user = UserProfile(
            id="user-faculty-1",
            email="joseph.jackson@skillsup.in",
            display_name="Joseph Jackson",
            hashed_password=pwd_hash,
            role="faculty",
            title="Senior Full Stack & Cloud Architect",
            avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
            bio="Specializing in React, TypeScript, Cloud Infrastructure with 10+ years teaching experience."
        )
        session.add(faculty_user)

        student_user = UserProfile(
            id="user-student-1",
            email="aarav.sharma@example.com",
            display_name="Aarav Sharma",
            hashed_password=pwd_hash,
            role="student",
            title="Computer Science Undergraduate",
            avatar="https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&w=400&q=80",
            bio="Enthusiastic CS learner focused on Web Development and Cloud Systems."
        )
        session.add(student_user)

        # 3. Memberships
        session.add(InstitutionMembership(
            institution_id=inst.id,
            user_id=faculty_user.id,
            role="faculty"
        ))
        session.add(InstitutionMembership(
            institution_id=inst.id,
            user_id=student_user.id,
            role="student"
        ))

        # 4. Students
        students_info = [
            ("stud-1", "STU-1001", "Aarav Sharma", "aarav.sharma@example.com", 96.0, 92.0),
            ("stud-2", "STU-1002", "Tanvi Verma", "tanvi.v@example.com", 100.0, 98.0),
            ("stud-3", "STU-1003", "Devansh Kulkarni", "devansh.k@example.com", 84.0, 78.0),
            ("stud-4", "STU-1004", "Meera Nambiar", "meera.n@example.com", 92.0, 88.0),
            ("stud-5", "STU-1005", "Rohan Deshmukh", "rohan.d@example.com", 71.0, 64.0),
            ("stud-6", "STU-1006", "Ananya Pillai", "ananya.p@example.com", 95.0, 90.0),
        ]

        for sid, sref, sname, semail, satt, squiz in students_info:
            st = Student(
                id=sid,
                institution_id=inst.id,
                external_ref=sref,
                display_name=sname,
                email=semail,
                cohort_code="2025-CS",
                enrollment_status="active",
                attendance_rate=satt,
                quiz_score_avg=squiz
            )
            session.add(st)

        # 5. Student Account Link (Aarav Sharma -> student_user)
        session.add(StudentAccountLink(
            institution_id=inst.id,
            student_id="stud-1",
            user_id=student_user.id
        ))

        # 6. Courses
        c1 = Course(
            id="course-1",
            institution_id=inst.id,
            code="CS402",
            title="The Complete 2025 Full-Stack Web Development Bootcamp",
            category="Computer Science & IT",
            credits=4,
            semester="Fall 2025",
            primary_faculty_id=faculty_user.id
        )
        c2 = Course(
            id="course-2",
            institution_id=inst.id,
            code="DB301",
            title="Advanced Database Management, SQL & Query Optimization",
            category="Data & Analytics",
            credits=4,
            semester="Fall 2025",
            primary_faculty_id=faculty_user.id
        )
        session.add(c1)
        session.add(c2)

        # 7. Sections
        sec1 = CourseSection(
            id="sec-1",
            institution_id=inst.id,
            course_id=c1.id,
            faculty_id=faculty_user.id,
            section_code="CS402-A",
            name="CS402: Full-Stack React Architecture",
            term="Jun 1, 2025 - Jul 15, 2025",
            access_code="3mia24z9x0",
            subject="Computer Science",
            color="bg-blue-600"
        )
        sec2 = CourseSection(
            id="sec-2",
            institution_id=inst.id,
            course_id=c2.id,
            faculty_id=faculty_user.id,
            section_code="DB301-A",
            name="DB301: Advanced SQL & Query Optimizations",
            term="Jun 10, 2025 - Jul 25, 2025",
            access_code="8kdf71q4w2",
            subject="Data Systems",
            color="bg-emerald-600"
        )
        session.add(sec1)
        session.add(sec2)

        # 8. Enrollments (all 6 students in CS402-A; 3 in DB301-A)
        for sid, _, _, _, _, _ in students_info:
            session.add(CourseEnrollment(
                institution_id=inst.id,
                section_id=sec1.id,
                student_id=sid
            ))

        for sid in ["stud-1", "stud-2", "stud-5"]:
            session.add(CourseEnrollment(
                institution_id=inst.id,
                section_id=sec2.id,
                student_id=sid
            ))

        # 9. Attendance Records
        now = datetime.now(timezone.utc)
        for days_ago in range(5):
            d_str = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            session.add(StudentAttendanceRecord(
                institution_id=inst.id,
                section_id=sec1.id,
                student_id="stud-1",
                date=d_str,
                status="Present",
                recorded_by=faculty_user.id
            ))
            # Rohan Deshmukh is absent on recent days
            session.add(StudentAttendanceRecord(
                institution_id=inst.id,
                section_id=sec1.id,
                student_id="stud-5",
                date=d_str,
                status="Absent" if days_ago < 3 else "Present",
                recorded_by=faculty_user.id
            ))

        # 10. Assessments
        a1 = Assessment(
            id="assess-1",
            institution_id=inst.id,
            section_id=sec1.id,
            title="React 19 Component Architecture Lab",
            assessment_type="quiz",
            total_marks=100.0,
            clo_code="CLO-1",
            due_at=now + timedelta(days=4),
            created_by=faculty_user.id
        )
        a2 = Assessment(
            id="assess-2",
            institution_id=inst.id,
            section_id=sec1.id,
            title="REST API Design & PostgreSQL Modeling",
            assessment_type="assignment",
            total_marks=100.0,
            clo_code="CLO-2",
            due_at=now + timedelta(days=10),
            created_by=faculty_user.id
        )
        session.add(a1)
        session.add(a2)

        # 11. Submissions
        session.add(AssessmentSubmission(
            institution_id=inst.id,
            assessment_id=a1.id,
            student_id="stud-1",
            score=94.0,
            feedback="Great work on custom hooks and state management.",
            graded_by=faculty_user.id
        ))
        session.add(AssessmentSubmission(
            institution_id=inst.id,
            assessment_id=a1.id,
            student_id="stud-5",
            score=58.0,
            feedback="Missing error boundaries and async cleanup.",
            graded_by=faculty_user.id
        ))

        # 12. Support Request (Aarav -> Joseph)
        session.add(SupportRequest(
            id="sup-1",
            institution_id=inst.id,
            student_id="stud-1",
            faculty_id=faculty_user.id,
            course_id=c1.id,
            category="concept_doubt",
            preferred_slot="Tomorrow 4:00 PM IST",
            student_note="Could you clarify optimistic UI updates and server transitions in React 19?",
            status="scheduled",
            faculty_response="Sure Aarav, let's connect on Zoom during tomorrow's office hours."
        ))

        # 13. Risk Signal (Rohan Deshmukh - attention suggested!)
        session.add(Signal(
            id="sig-1",
            institution_id=inst.id,
            student_id="stud-5",
            rule_key="ATTENDANCE_BELOW_75",
            result="attention_suggested",
            ml_risk_probability=0.79,
            ml_tier="HIGH",
            evidence_snapshot='{"attendance_rate": 0.71, "missed_days_streak": 3, "quiz_score": 58}',
            reviewed=False
        ))

        # 14. Support Case
        session.add(Case(
            id="case-1",
            institution_id=inst.id,
            student_id="stud-5",
            originating_signal_id="sig-1",
            selected_intervention_key="mentor_check_in",
            state="assigned",
            primary_owner_user_id=faculty_user.id,
            due_at=now + timedelta(days=5),
            deadline_version=1,
            version=1
        ))

        # 15. Follow up
        session.add(FollowUp(
            id="fol-1",
            institution_id=inst.id,
            case_id="case-1",
            follow_up_type="contact_attempt",
            contact_status="student_reached",
            proof_kind="staff_attestation",
            sanitized_note="Sent check-in email regarding consecutive absences. Student replied citing transit illness.",
            recorded_by=faculty_user.id,
            occurred_at=now - timedelta(hours=12)
        ))

        # 16. Notifications
        session.add(Notification(
            institution_id=inst.id,
            user_id=student_user.id,
            title="Assessment Scheduled: React 19 Component Architecture Lab",
            message="Your lab assignment is scheduled and due in 4 days.",
            type="info"
        ))
        session.add(Notification(
            institution_id=inst.id,
            user_id=faculty_user.id,
            title="Risk Alert: 1 Student in CS402 Requires Attention",
            message="Rohan Deshmukh's attendance dropped to 71%. Review signal.",
            type="alert"
        ))

        # 17. Processing Authorizations
        from app.models.entities import (
            ProcessingAuthorization,
            StudentObservation,
            PolicyVersion,
            EvidencePacket,
            CaseTask,
            PulseQuestionnaire,
            PulsePeriod,
            PointsLedgerEntry,
            RewardCatalogItem,
            DocumentRecord,
            StudentIdentity
        )
        import hashlib
        import json

        session.add(ProcessingAuthorization(
            institution_id=inst.id,
            student_id="stud-1",
            purpose_key="early_warning",
            status="active"
        ))
        session.add(ProcessingAuthorization(
            institution_id=inst.id,
            student_id="stud-5",
            purpose_key="early_warning",
            status="active"
        ))

        # 18. Student Observations
        session.add(StudentObservation(
            institution_id=inst.id,
            student_id="stud-5",
            domain="attendance",
            metric_key="attendance_rate",
            value=71.0,
            unit="percentage",
            event_at=now - timedelta(days=2),
            available_at=now - timedelta(days=1),
            quality_state="valid",
            source_system="lms_sync",
            source_record_ref="att-2026-10-stud-5",
            source_version=1
        ))

        # 19. Policy Version & Evidence Packet
        rules = [
            {"rule_key": "ATTENDANCE_BELOW_75", "metric": "attendance_rate", "op": "<", "threshold": 75.0, "reason": "ATTENDANCE_BELOW_75"}
        ]
        def_str = json.dumps(rules, sort_keys=True)
        policy_checksum = hashlib.sha256(def_str.encode("utf-8")).hexdigest()
        pv = PolicyVersion(
            id="policy-1",
            institution_id=inst.id,
            policy_key="ug_attendance_academic_v1",
            version=1,
            definition_json=def_str,
            checksum=policy_checksum,
            status="published"
        )
        session.add(pv)

        snapshot_dict = {"student_id": "stud-5", "attendance_rate": 71.0, "rule": "ATTENDANCE_BELOW_75"}
        snap_canonical = json.dumps(snapshot_dict, sort_keys=True)
        snap_digest = hashlib.sha256(snap_canonical.encode("utf-8")).hexdigest()
        session.add(EvidencePacket(
            id="ev-1",
            institution_id=inst.id,
            student_id="stud-5",
            policy_version_id="policy-1",
            as_of_at=now,
            snapshot_json=snap_canonical,
            digest=snap_digest
        ))

        # 20. Case Task
        session.add(CaseTask(
            id="task-1",
            institution_id=inst.id,
            case_id="case-1",
            domain="academic",
            generic_label="Academic Check-in & Attendance Remediation Plan",
            state="pending",
            assignee_user_id=faculty_user.id,
            due_at=now + timedelta(days=3)
        ))

        # 21. Wellbeing Pulse Instrument & Active Period
        session.add(PulsePeriod(
            id="period-w44",
            institution_id=inst.id,
            period_key="2026-W44",
            label="Reporting Week 44, October 2026",
            starts_at=now - timedelta(days=3),
            ends_at=now + timedelta(days=4),
            is_active=True
        ))
        session.add(PulseQuestionnaire(
            id="quest-1",
            institution_id=inst.id,
            version="v1.0-weekly",
            title="Weekly Student Wellbeing Pulse",
            questions_json=json.dumps([
                {"dimension": "emotional_wellbeing", "label": "How would you rate your general mood and emotional calm this week?"},
                {"dimension": "belonging_community", "label": "I felt connected to my peers and instructors this week."},
                {"dimension": "academic_experience", "label": "I feel confident keeping pace with my coursework and assignments."},
                {"dimension": "support_trust", "label": "If I struggled this week, I know where to turn for academic or peer help."},
                {"dimension": "safety_respect", "label": "I feel respected and secure in my campus learning environment."},
                {"dimension": "growth_confidence", "label": "I feel I am making steady progress toward my academic milestones."}
            ]),
            active=True
        ))

        # 22. Rewards Ledger & Catalog
        session.add(PointsLedgerEntry(
            institution_id=inst.id,
            student_id="stud-1",
            activity_key="verified_learning",
            points=25,
            source_ref="workshop-react-19"
        ))
        session.add(PointsLedgerEntry(
            institution_id=inst.id,
            student_id="stud-1",
            activity_key="weekly_pulse",
            points=10,
            source_ref="pulse-2026-W43"
        ))
        session.add(RewardCatalogItem(
            id="rew-1",
            institution_id=inst.id,
            sku="DISHA-STICKER-PACK",
            title="DISHA Holographic Engineering Sticker Pack",
            category="stationery",
            points_cost=20,
            stock=100,
            active=True
        ))
        session.add(RewardCatalogItem(
            id="rew-2",
            institution_id=inst.id,
            sku="CAMPUS-MUG",
            title="Matte Ceramic Campus Coffee Mug",
            category="merchandise",
            points_cost=50,
            stock=30,
            active=True
        ))

        # 23. Document Record & Student Identity
        doc_hash = hashlib.sha256(b"INTERVENTION_PLAN_ROHAN_DESHMUKH_OCT_2026").hexdigest()
        session.add(DocumentRecord(
            id="doc-1",
            institution_id=inst.id,
            document_ref="DOC-PLAN-2026-001",
            title="Intervention Plan: Attendance Remediation (Fall 2025)",
            doc_type="intervention_plan",
            storage_key="documents/campus-1/plan-2026-001.pdf",
            sha256_hash=doc_hash,
            status="finalized",
            created_by=faculty_user.id
        ))

        session.add(StudentIdentity(
            id="ident-1",
            institution_id=inst.id,
            user_id=student_user.id,
            disha_id="DISHA-STU-8821-4491",
            display_name="Scholar Aarav",
            avatar_config_json=json.dumps({"theme": "aurora", "badge": "apprentice", "halo": True})
        ))

        await session.commit()
        print("Seeding complete! Default campus, faculty, student, courses, and signals created.")


if __name__ == "__main__":
    asyncio.run(seed_data())
