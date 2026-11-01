"""
DISHA Model Reconciliation & Registration Test Suite

Tests:
1. SQLAlchemy metadata registration for all 16 canonical DISHA tables.
2. Duplicate table detection and verification of single source of truth for disha_interventions.
3. Clean model imports and backward compatibility aliases.
4. Foreign-key resolution across all registered tables.
5. SQLAlchemy ORM relationship configuration integrity (configure_mappers).
6. Complete async model instantiation, persistence, and querying in SQLite.
"""

import unittest
from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.orm import configure_mappers
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.modules.identity.models import User, Membership, IdentityEntity
from app.modules.roster.models import Student, Observation, RosterEntity
from app.modules.counselling.models import CounsellorProfile, CounsellorAssignment, CounsellingEntity
from app.modules.cases.models import (
    Case,
    CaseNote,
    CaseEvent,
    InterventionCatalogue,
    Intervention,
    InterventionOutcome,
    FollowUp,
    FollowUpNote,
    CasesEntity,
)
from app.modules.interventions.models import (
    Intervention as InterventionsModuleIntervention,
    InterventionCatalogue as InterventionsModuleCatalogue,
    InterventionOutcome as InterventionsModuleOutcome,
)
from app.modules.notifications.models import Notification, NotificationsEntity
from app.modules.audit.models import AuditEvent, AuditEntity
from app.modules.cases.models import Signal
from app.modules.faculty.models import (
    FacultyProfile,
    Course,
    CourseSection,
    CourseEnrollment,
    StudentAttendanceRecord,
    Assessment,
    AssessmentSubmission,
)
from app.modules.student.models import SupportRequest


class TestModelReconciliation(unittest.IsolatedAsyncioTestCase):

    EXPECTED_TABLES = {
        "disha_identity",
        "disha_memberships",
        "disha_roster",
        "disha_observations",
        "disha_counsellor_profiles",
        "disha_counsellor_assignments",
        "disha_cases",
        "disha_case_notes",
        "disha_case_events",
        "disha_intervention_catalogue",
        "disha_interventions",
        "disha_intervention_outcomes",
        "disha_followups",
        "disha_followup_notes",
        "disha_notifications",
        "disha_audit_events",
        "disha_faculty_profiles",
        "disha_courses",
        "disha_course_sections",
        "disha_course_enrollments",
        "disha_attendance_records",
        "disha_assessments",
        "disha_assessment_submissions",
        "disha_support_requests",
        "disha_signals",
    }

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    # 1. SQLAlchemy Metadata Registration
    def test_sqlalchemy_metadata_registration(self):
        """All 16 canonical DISHA tables must be present in Base.metadata.tables."""
        registered_tables = set(Base.metadata.tables.keys())
        missing_tables = self.EXPECTED_TABLES - registered_tables
        self.assertEqual(
            missing_tables,
            set(),
            f"Missing tables in Base.metadata: {missing_tables}",
        )
        for tbl in self.EXPECTED_TABLES:
            self.assertIn(tbl, registered_tables)

    # 2. Duplicate Table Detection & Authoritative Ownership
    def test_duplicate_table_detection(self):
        """disha_interventions and related entities must have a single authoritative definition."""
        # Check that Interventions module re-exports identical class objects from cases domain
        self.assertIs(
            InterventionsModuleIntervention,
            Intervention,
            "Intervention must be authoritatively defined in cases domain",
        )
        self.assertIs(
            InterventionsModuleCatalogue,
            InterventionCatalogue,
            "InterventionCatalogue must be authoritatively defined in cases domain",
        )
        self.assertIs(
            InterventionsModuleOutcome,
            InterventionOutcome,
            "InterventionOutcome must be authoritatively defined in cases domain",
        )

        # Verify no duplicate table names exist in metadata
        table_names = [table.name for table in Base.metadata.tables.values()]
        self.assertEqual(
            len(table_names),
            len(set(table_names)),
            "Duplicate table registrations detected in Base.metadata",
        )

    # 3. Model Import Integrity & Backward Compatibility
    def test_model_import_integrity_and_aliases(self):
        """Model imports must resolve cleanly and legacy aliases must map to authoritative models."""
        self.assertIs(IdentityEntity, User)
        self.assertIs(RosterEntity, Student)
        self.assertIs(CounsellingEntity, CounsellorProfile)
        self.assertIs(CasesEntity, Case)
        self.assertIs(NotificationsEntity, Notification)
        self.assertIs(AuditEntity, AuditEvent)

    def test_case_state_enum_integration(self):
        """Case model must integrate with the canonical 14-state CaseState enum."""
        from app.shared.enums import CaseState, CaseStatus
        case = Case(title="State Test")
        # Default status maps to ACTION_PLANNED
        self.assertEqual(case.state, CaseState.ACTION_PLANNED.value)

        # Setting canonical state updates underlying status
        case.state = CaseState.SUPPORT_IN_PROGRESS
        self.assertEqual(case.status, "support_in_progress")
        self.assertEqual(case.state, "support_in_progress")

        case.state = CaseState.CONTACT_ATTEMPTED
        self.assertEqual(case.status, "contact_attempted")
        self.assertEqual(case.state, "contact_attempted")

        case.state = CaseState.OUTCOME_REVIEWED
        self.assertEqual(case.status, "outcome_reviewed")
        self.assertEqual(case.state, "outcome_reviewed")

    # 4. Foreign-Key Resolution
    def test_foreign_key_resolution(self):
        """All foreign keys defined on all tables must resolve to valid target tables and columns."""
        for table_name in self.EXPECTED_TABLES:
            table = Base.metadata.tables[table_name]
            for fk in table.foreign_keys:
                target_col = fk.column
                self.assertIsNotNone(
                    target_col,
                    f"Foreign key '{fk}' in '{table_name}' failed to resolve to a target column",
                )
                self.assertIn(
                    target_col.table.name,
                    Base.metadata.tables,
                    f"Target table '{target_col.table.name}' for FK in '{table_name}' not registered",
                )

    # 5. Relationship Configuration
    def test_relationship_configuration(self):
        """SQLAlchemy configure_mappers() must execute without errors."""
        try:
            configure_mappers()
        except Exception as e:
            self.fail(f"configure_mappers() failed: {e}")

        # Check relationships on User
        user_mapper = User.__mapper__
        self.assertIn("memberships", user_mapper.relationships)

        # Check relationships on Student
        student_mapper = Student.__mapper__
        self.assertIn("observations", student_mapper.relationships)

        # Check relationships on Case
        case_mapper = Case.__mapper__
        self.assertIn("notes", case_mapper.relationships)
        self.assertIn("events", case_mapper.relationships)
        self.assertIn("interventions", case_mapper.relationships)
        self.assertIn("followups", case_mapper.relationships)
        self.assertIn("student", case_mapper.relationships)
        self.assertIn("assigned_counsellor", case_mapper.relationships)

        # Check relationships on Intervention
        intervention_mapper = Intervention.__mapper__
        self.assertIn("case", intervention_mapper.relationships)
        self.assertIn("catalogue_entry", intervention_mapper.relationships)
        self.assertIn("outcome", intervention_mapper.relationships)

        # Check relationships on FollowUp
        followup_mapper = FollowUp.__mapper__
        self.assertIn("case", followup_mapper.relationships)
        self.assertIn("followup_notes", followup_mapper.relationships)

    # 6. Model Instantiation & Persistence
    async def test_full_model_instantiation_and_persistence(self):
        """Verify full lifecycle persistence and relationship retrieval across all models."""
        async with self.async_session() as session:
            async with session.begin():
                # 1. Identity & Membership
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email="counsellor@disha.edu",
                    hashed_password="$argon2id$mockhash",
                    full_name="Dr. Anita Desai",
                    is_active=True,
                )
                session.add(user)

                membership = Membership(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    campus_id="campus-main",
                    role="counsellor",
                    department="Psychology",
                    is_active=True,
                )
                session.add(membership)

                # 2. Roster & Observations
                student_id = str(uuid.uuid4())
                student = Student(
                    id=student_id,
                    campus_id="campus-main",
                    student_uid="STU-2026-0042",
                    full_name="Rohan Verma",
                    email="rohan@student.disha.edu",
                    department="Computer Science",
                    course="B.Tech",
                    academic_year=3,
                    is_active=True,
                )
                session.add(student)

                observation = Observation(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    campus_id="campus-main",
                    domain="attendance",
                    source="SIS-LMS",
                    data="Attendance dropped below 75% in three consecutive weeks",
                    observed_at=datetime.now(timezone.utc),
                )
                session.add(observation)

                # 3. Counselling Profile & Assignment
                profile = CounsellorProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    campus_id="campus-main",
                    department="Student Welfare",
                    specialisation="Academic Stress & Attendance",
                    is_active=True,
                )
                session.add(profile)

                assignment = CounsellorAssignment(
                    id=str(uuid.uuid4()),
                    counsellor_id=user_id,
                    student_id=student_id,
                    campus_id="campus-main",
                    is_active=True,
                )
                session.add(assignment)

                # 4. Case Management
                case_id = str(uuid.uuid4())
                case = Case(
                    id=case_id,
                    campus_id="campus-main",
                    student_id=student_id,
                    assigned_counsellor_id=user_id,
                    status="in_progress",
                    priority="high",
                    title="Attendance Intervention - Rohan Verma",
                    description="Chronic absenteeism flagged by automated early warning rules",
                    version=1,
                )
                session.add(case)

                note = CaseNote(
                    id=str(uuid.uuid4()),
                    case_id=case_id,
                    author_id=user_id,
                    campus_id="campus-main",
                    content="Initial assessment conducted via Google Meet",
                )
                session.add(note)

                event = CaseEvent(
                    id=str(uuid.uuid4()),
                    case_id=case_id,
                    actor_id=user_id,
                    campus_id="campus-main",
                    event_type="status_changed",
                    payload={"from": "assigned", "to": "in_progress"},
                )
                session.add(event)

                # 5. Intervention & Outcomes
                catalogue_id = str(uuid.uuid4())
                catalogue = InterventionCatalogue(
                    id=catalogue_id,
                    name="Attendance Monitoring & Coaching",
                    description="Weekly check-ins to monitor LMS participation and attendance",
                    category="attendance",
                    is_active=True,
                )
                session.add(catalogue)

                intervention_id = str(uuid.uuid4())
                intervention = Intervention(
                    id=intervention_id,
                    case_id=case_id,
                    catalogue_id=catalogue_id,
                    counsellor_id=user_id,
                    campus_id="campus-main",
                    description="Four-week structured study and morning routine plan",
                    progress="completed",
                )
                session.add(intervention)

                outcome = InterventionOutcome(
                    id=str(uuid.uuid4()),
                    case_id=case_id,
                    intervention_id=intervention_id,
                    counsellor_id=user_id,
                    campus_id="campus-main",
                    completion_status="successful",
                    outcome_notes="Student attendance restored to 88%",
                    completed_at=datetime.now(timezone.utc),
                )
                session.add(outcome)

                # 6. Follow-up & Follow-up Notes
                followup_id = str(uuid.uuid4())
                followup = FollowUp(
                    id=followup_id,
                    case_id=case_id,
                    counsellor_id=user_id,
                    campus_id="campus-main",
                    title="Mid-term attendance audit follow-up",
                    scheduled_at=datetime.now(timezone.utc),
                    status="completed",
                )
                session.add(followup)

                fnote = FollowUpNote(
                    id=str(uuid.uuid4()),
                    followup_id=followup_id,
                    case_id=case_id,
                    author_id=user_id,
                    campus_id="campus-main",
                    content="Verified student presence in lab classes",
                )
                session.add(fnote)

                # 7. Notification & Audit
                notification = Notification(
                    id=str(uuid.uuid4()),
                    recipient_id=user_id,
                    campus_id="campus-main",
                    notification_type="case_assigned",
                    reference_id=case_id,
                    reference_type="case",
                    title="New High Priority Case Assigned",
                    body="You have been assigned to Rohan Verma",
                    is_read=False,
                    idempotency_key=f"notif-{case_id}-{user_id}",
                )
                session.add(notification)

                audit_event = AuditEvent(
                    id=str(uuid.uuid4()),
                    actor_id=user_id,
                    campus_id="campus-main",
                    entity_type="case",
                    entity_id=case_id,
                    action="case.created",
                    event_metadata={"priority": "high", "campus": "campus-main"},
                    correlation_id=str(uuid.uuid4()),
                    prev_hash=None,
                    event_hash="abc123hash",
                )
                session.add(audit_event)

        # Verification step: Retrieve and assert persisted entities
        async with self.async_session() as session:
            # Query User and Membership
            user_res = await session.execute(select(User).where(User.id == user_id))
            saved_user = user_res.scalar_one()
            self.assertEqual(saved_user.email, "counsellor@disha.edu")
            self.assertEqual(len(saved_user.memberships), 1)
            self.assertEqual(saved_user.memberships[0].role, "counsellor")

            # Query Student and Observation
            student_res = await session.execute(select(Student).where(Student.id == student_id))
            saved_student = student_res.scalar_one()
            self.assertEqual(saved_student.student_uid, "STU-2026-0042")
            self.assertEqual(len(saved_student.observations), 1)
            self.assertEqual(saved_student.observations[0].domain, "attendance")

            # Query Case and its relations
            case_res = await session.execute(select(Case).where(Case.id == case_id))
            saved_case = case_res.scalar_one()
            self.assertEqual(saved_case.title, "Attendance Intervention - Rohan Verma")
            self.assertEqual(len(saved_case.notes), 1)
            self.assertEqual(len(saved_case.events), 1)
            self.assertEqual(len(saved_case.interventions), 1)
            self.assertEqual(len(saved_case.followups), 1)
            self.assertEqual(saved_case.student.full_name, "Rohan Verma")
            self.assertEqual(saved_case.assigned_counsellor.full_name, "Dr. Anita Desai")

            # Query Intervention and Outcome
            saved_intervention = saved_case.interventions[0]
            self.assertEqual(saved_intervention.progress, "completed")
            self.assertIsNotNone(saved_intervention.outcome)
            self.assertEqual(saved_intervention.outcome.completion_status, "successful")
            self.assertEqual(saved_intervention.catalogue_entry.name, "Attendance Monitoring & Coaching")

            # Query FollowUp and Notes
            saved_followup = saved_case.followups[0]
            self.assertEqual(len(saved_followup.followup_notes), 1)

            # Query Notification
            notif_res = await session.execute(
                select(Notification).where(Notification.recipient_id == user_id)
            )
            saved_notif = notif_res.scalar_one()
            self.assertEqual(saved_notif.notification_type, "case_assigned")
            self.assertEqual(saved_notif.recipient.full_name, "Dr. Anita Desai")

            # Query Audit Event
            audit_res = await session.execute(
                select(AuditEvent).where(AuditEvent.entity_id == case_id)
            )
            saved_audit = audit_res.scalar_one()
            self.assertEqual(saved_audit.action, "case.created")
            self.assertEqual(saved_audit.event_metadata["priority"], "high")


if __name__ == "__main__":
    unittest.main()

