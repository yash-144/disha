"""
DISHA Case Persistence, Atomic Optimistic Concurrency, and Transaction Integrity Tests

Verifies:
1. Database-backed case creation with transactional CaseEvent and AuditEvent.
2. Case retrieval and relationship loading after clean session reload.
3. Case listing and access control enforcing strict campus-level tenancy isolation.
4. Step-by-step state transitions with atomic database persistence and version incrementing.
5. Database-level optimistic locking rejecting stale expected_version with ConcurrencyConflictError (HTTP 409).
6. ACID transaction rollback: Case mutation is aborted if CaseEvent insertion fails.
7. ACID transaction rollback: Case mutation is aborted if AuditEvent insertion fails.
8. Notification outbox consistency (recipient, unread, unsent, unique idempotency key).
9. Authorization and confidentiality: confidential counselling notes are isolated to disha_case_notes
   and never leaked into AuditEvent metadata or Notification payloads; unauthorized roles are rejected.
10. Round-trip persistence and property projection for all 14 canonical CaseState values.
"""

import unittest
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.shared.enums import CaseState, CaseStatus, map_status_to_state, map_state_to_status
from app.shared.utils import utc_now
from app.core.permissions import Role
from app.core.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ConcurrencyConflictError,
    StateTransitionError,
)
from app.modules.identity.models import User, Membership
from app.modules.roster.models import Student
from app.modules.cases.models import Case, CaseNote, CaseEvent
from app.modules.audit.models import AuditEvent
from app.modules.notifications.models import Notification, NotificationOutbox
from app.modules.cases.schemas import (
    CaseCreateRequest,
    CaseUpdateRequest,
    CaseAssignRequest,
    CaseReopenRequest,
    CaseDismissRequest,
)
from app.modules.cases.services import CaseService, case_to_detail_response


class TestCasesPersistenceAndIntegrity(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # In-memory SQLite async engine for fast, isolated unit verification
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.campus_1 = "campus-ipp-01"
        self.campus_2 = "campus-ipp-02"

        self.student_1_id = str(uuid.uuid4())
        self.student_2_id = str(uuid.uuid4())
        self.counsellor_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())
        self.student_user_id = str(uuid.uuid4())

        async with self.async_session() as session:
            async with session.begin():
                s1 = Student(
                    id=self.student_1_id,
                    campus_id=self.campus_1,
                    student_uid="STU-001",
                    full_name="Aarav Sharma",
                    department="Computer Science",
                    course="B.Tech",
                    academic_year=2,
                    is_active=True,
                )
                s2 = Student(
                    id=self.student_2_id,
                    campus_id=self.campus_2,
                    student_uid="STU-002",
                    full_name="Diya Patel",
                    department="Electronics",
                    course="B.Tech",
                    academic_year=3,
                    is_active=True,
                )
                counsellor = User(
                    id=self.counsellor_id,
                    email="counsellor@disha.edu",
                    hashed_password="argon2_fake_hash",
                    full_name="Priya Nair",
                    is_active=True,
                )
                admin = User(
                    id=self.admin_id,
                    email="admin@disha.edu",
                    hashed_password="argon2_fake_hash",
                    full_name="Vikram Mehta",
                    is_active=True,
                )
                student_user = User(
                    id=self.student_user_id,
                    email="aarav@disha.edu",
                    hashed_password="argon2_fake_hash",
                    full_name="Aarav Sharma",
                    is_active=True,
                )
                session.add_all([s1, s2, counsellor, admin, student_user])

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_database_backed_case_creation(self):
        """Verify Case is created in database with transactional CaseEvent and AuditEvent."""
        async with self.async_session() as session:
            req = CaseCreateRequest(
                student_id=self.student_1_id,
                title="Academic Stress and Drop in Attendance",
                description="Student has missed 4 consecutive lectures.",
                priority="high",
                initial_state=CaseState.ACTION_PLANNED.value,
                assigned_counsellor_id=self.counsellor_id,
                due_date=utc_now() + timedelta(days=5),
            )
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=req,
            )
            self.assertIsNotNone(case.id)
            self.assertEqual(case.campus_id, self.campus_1)
            self.assertEqual(case.version, 1)
            self.assertEqual(case.status, CaseState.ACTION_PLANNED.value)

            # Check CaseEvent
            event_res = await session.execute(
                select(CaseEvent).where(CaseEvent.case_id == case.id)
            )
            events = event_res.scalars().all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, "CASE_CREATED")

            # Check AuditEvent
            audit_res = await session.execute(
                select(AuditEvent).where(AuditEvent.entity_id == case.id)
            )
            audits = audit_res.scalars().all()
            self.assertEqual(len(audits), 1)
            self.assertEqual(audits[0].action, "CASE_CREATED")

            # Check Notification outbox
            notif_res = await session.execute(
                select(NotificationOutbox).where(NotificationOutbox.case_id == case.id)
            )
            notifs = notif_res.scalars().all()
            self.assertEqual(len(notifs), 1)
            self.assertEqual(notifs[0].recipient_id, self.counsellor_id)
            self.assertEqual(notifs[0].status, "pending")
            self.assertEqual(notifs[0].adapter_key, "in_app")

    async def test_case_retrieval_after_session_reload(self):
        """Verify case data and relationships reload accurately across session boundaries."""
        case_id = None
        async with self.async_session() as session1:
            req = CaseCreateRequest(
                student_id=self.student_1_id,
                title="Exam Anxiety Support",
                priority="medium",
                initial_state=CaseState.ACTION_PLANNED.value,
            )
            case = await CaseService.create_case(
                db=session1,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=req,
            )
            case_id = case.id

        # Open completely fresh session
        async with self.async_session() as session2:
            reloaded = await CaseService.get_case(
                db=session2,
                case_id=case_id,
                campus_id=self.campus_1,
            )
            self.assertEqual(reloaded.id, case_id)
            self.assertEqual(reloaded.student.full_name, "Aarav Sharma")
            self.assertEqual(reloaded.state, CaseState.ACTION_PLANNED.value)
            self.assertEqual(reloaded.legacy_status, CaseStatus.NEW.value)

            resp = case_to_detail_response(reloaded)
            self.assertEqual(resp.student_name, "Aarav Sharma")
            self.assertEqual(resp.department, "Computer Science")
            self.assertEqual(resp.state, CaseState.ACTION_PLANNED)
            self.assertEqual(resp.legacy_status, CaseStatus.NEW)

    async def test_case_listing_with_campus_isolation(self):
        """Verify strict campus-level tenancy isolation on listing and direct retrieval."""
        async with self.async_session() as session:
            # Create case in Campus 1
            c1 = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Campus 1 Case",
                ),
            )
            # Create case in Campus 2
            c2 = await CaseService.create_case(
                db=session,
                campus_id=self.campus_2,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_2_id,
                    title="Campus 2 Case",
                ),
            )

            # Query list for Campus 1
            list_c1 = await CaseService.list_cases(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
            )
            self.assertEqual(len(list_c1), 1)
            self.assertEqual(list_c1[0].id, c1.id)

            # Query list for Campus 2
            list_c2 = await CaseService.list_cases(
                db=session,
                campus_id=self.campus_2,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
            )
            self.assertEqual(len(list_c2), 1)
            self.assertEqual(list_c2[0].id, c2.id)

            # Attempt to access Campus 2 case with Campus 1 tenancy -> EntityNotFoundError (HTTP 404)
            with self.assertRaises(EntityNotFoundError):
                await CaseService.get_case(
                    db=session,
                    case_id=c2.id,
                    campus_id=self.campus_1,
                )

    async def test_state_transitions_and_persistence(self):
        """Verify sequential 14-state lifecycle transitions persist with version incrementing."""
        now = utc_now()
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Lifecycle Progression Test",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )
            self.assertEqual(case.version, 1)

            # 1. ACTION_PLANNED -> ASSIGNED
            res1 = await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                target_state_raw=CaseState.ASSIGNED.value,
                expected_version=1,
                new_owner_id=self.counsellor_id,
                due_at=now + timedelta(days=3),
            )
            self.assertEqual(res1["case"]["state"], CaseState.ASSIGNED.value)
            self.assertEqual(res1["case"]["version"], 2)

            # 2. ASSIGNED -> ACCEPTED
            res2 = await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                target_state_raw=CaseState.ACCEPTED.value,
                expected_version=2,
            )
            self.assertEqual(res2["case"]["state"], CaseState.ACCEPTED.value)
            self.assertEqual(res2["case"]["version"], 3)

            # 3. ACCEPTED -> SUPPORT_IN_PROGRESS
            res3 = await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                target_state_raw=CaseState.SUPPORT_IN_PROGRESS.value,
                expected_version=3,
            )
            self.assertEqual(res3["case"]["state"], CaseState.SUPPORT_IN_PROGRESS.value)
            self.assertEqual(res3["case"]["version"], 4)

            # 4. SUPPORT_IN_PROGRESS -> OUTCOME_REVIEWED (with outcome and follow-up flags)
            res4 = await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                target_state_raw=CaseState.OUTCOME_REVIEWED.value,
                expected_version=4,
                has_outcome=True,
                has_follow_up=True,
                notes="Completed 3 counseling sessions with positive progress.",
            )
            self.assertEqual(res4["case"]["state"], CaseState.OUTCOME_REVIEWED.value)
            self.assertEqual(res4["case"]["version"], 5)

            # 5. OUTCOME_REVIEWED -> CLOSED
            res5 = await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                target_state_raw=CaseState.CLOSED.value,
                expected_version=5,
                has_outcome=True,
                notes="Goals achieved. Closing case.",
            )
            self.assertEqual(res5["case"]["state"], CaseState.CLOSED.value)
            self.assertEqual(res5["case"]["version"], 6)

            # Verify events stored in DB
            events = await CaseService.get_case_events(session, case.id, self.campus_1)
            # 1 create + 5 transitions = 6 events
            self.assertEqual(len(events), 6)

    async def test_concurrent_updates_with_stale_versions(self):
        """Verify database-level optimistic locking rejects stale version updates with HTTP 409."""
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Concurrency Verification Case",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )
            self.assertEqual(case.version, 1)

            # First update succeeds: v1 -> v2
            updated = await CaseService.update_case(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseUpdateRequest(
                    expected_version=1,
                    title="Updated Title 1",
                ),
            )
            self.assertEqual(updated.version, 2)

            # Second update using stale expected_version=1 MUST raise ConcurrencyConflictError (HTTP 409)
            with self.assertRaises(ConcurrencyConflictError):
                await CaseService.update_case(
                    db=session,
                    case_id=case.id,
                    campus_id=self.campus_1,
                    actor_id=self.admin_id,
                    actor_roles=[Role.INSTITUTION_ADMIN.value],
                    data=CaseUpdateRequest(
                        expected_version=1,  # Stale version!
                        title="Conflicting Title Update",
                    ),
                )

            # Transition using stale expected_version=1 MUST also raise ConcurrencyConflictError (HTTP 409)
            with self.assertRaises(ConcurrencyConflictError):
                await CaseService.transition_case_db(
                    db=session,
                    case_id=case.id,
                    campus_id=self.campus_1,
                    actor_user_id=self.admin_id,
                    actor_roles=[Role.INSTITUTION_ADMIN.value],
                    target_state_raw=CaseState.ASSIGNED.value,
                    expected_version=1,  # Stale!
                    new_owner_id=self.counsellor_id,
                    due_at=utc_now() + timedelta(days=2),
                )

            # Verify row version is still 2 and title is "Updated Title 1"
            fresh = await CaseService.get_case(session, case.id, self.campus_1)
            self.assertEqual(fresh.version, 2)
            self.assertEqual(fresh.title, "Updated Title 1")

    async def test_atomic_rollback_when_case_event_fails(self):
        """Verify ACID rollback: if CaseEvent fails, Case state & version remain unchanged."""
        case_id = None
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Rollback Test Case",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )
            self.assertEqual(case.version, 1)
            case_id = case.id

            # Simulate CaseEvent failure via session.add interceptor
            orig_add = session.add
            def mock_add(instance):
                if isinstance(instance, CaseEvent):
                    raise RuntimeError("Simulated CaseEvent insertion failure")
                return orig_add(instance)

            session.add = mock_add
            with self.assertRaises(RuntimeError):
                await CaseService.transition_case_db(
                    db=session,
                    case_id=case_id,
                    campus_id=self.campus_1,
                    actor_user_id=self.admin_id,
                    actor_roles=[Role.INSTITUTION_ADMIN.value],
                    target_state_raw=CaseState.ASSIGNED.value,
                    expected_version=1,
                    new_owner_id=self.counsellor_id,
                    due_at=utc_now() + timedelta(days=2),
                )
            session.add = orig_add

        # In a completely fresh session, confirm rollback: status is still ACTION_PLANNED and version is 1
        async with self.async_session() as fresh_session:
            fresh = await CaseService.get_case(fresh_session, case_id, self.campus_1)
            self.assertEqual(fresh.status, CaseState.ACTION_PLANNED.value)
            self.assertEqual(fresh.version, 1)

            # Confirm no second event was committed
            events = await fresh_session.scalars(
                select(CaseEvent).where(CaseEvent.case_id == case_id)
            )
            self.assertEqual(len(events.all()), 1)

    async def test_atomic_rollback_when_audit_event_fails(self):
        """Verify ACID rollback: if AuditEvent fails, Case state & CaseEvent are completely rolled back."""
        case_id = None
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Audit Rollback Test Case",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )
            self.assertEqual(case.version, 1)
            case_id = case.id

            # Simulate AuditEvent failure via session.add interceptor
            orig_add = session.add
            def mock_add(instance):
                if isinstance(instance, AuditEvent):
                    raise RuntimeError("Simulated AuditEvent insertion failure")
                return orig_add(instance)

            session.add = mock_add
            with self.assertRaises(RuntimeError):
                await CaseService.transition_case_db(
                    db=session,
                    case_id=case_id,
                    campus_id=self.campus_1,
                    actor_user_id=self.admin_id,
                    actor_roles=[Role.INSTITUTION_ADMIN.value],
                    target_state_raw=CaseState.ASSIGNED.value,
                    expected_version=1,
                    new_owner_id=self.counsellor_id,
                    due_at=utc_now() + timedelta(days=2),
                )
            session.add = orig_add

        # In a completely fresh session, confirm rollback: status is still ACTION_PLANNED and version is 1
        async with self.async_session() as fresh_session:
            fresh = await CaseService.get_case(fresh_session, case_id, self.campus_1)
            self.assertEqual(fresh.status, CaseState.ACTION_PLANNED.value)
            self.assertEqual(fresh.version, 1)

            # Confirm no second event or audit was committed
            events = await fresh_session.scalars(
                select(CaseEvent).where(CaseEvent.case_id == case_id)
            )
            self.assertEqual(len(events.all()), 1)
            audits = await fresh_session.scalars(
                select(AuditEvent).where(AuditEvent.entity_id == case_id)
            )
            self.assertEqual(len(audits.all()), 1)

    async def test_notification_outbox_consistency(self):
        """Verify Notification outbox consistency (correct recipient, unread, unsent, idempotency key)."""
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Notification Outbox Verification",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )

            # Transition to ASSIGNED
            await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                target_state_raw=CaseState.ASSIGNED.value,
                expected_version=1,
                new_owner_id=self.counsellor_id,
                due_at=utc_now() + timedelta(days=3),
            )

            # Verify notification record
            notif_res = await session.execute(
                select(NotificationOutbox).where(NotificationOutbox.case_id == case.id)
            )
            notifs = notif_res.scalars().all()
            self.assertEqual(len(notifs), 1)
            notif = notifs[0]
            self.assertEqual(notif.recipient_id, self.counsellor_id)
            self.assertEqual(notif.status, "pending")
            self.assertIsNone(notif.sent_at)
            self.assertEqual(notif.template_key, "CASE_ASSIGNED")
            self.assertIn("v2-assigned", notif.idempotency_key)

    async def test_authorization_and_confidentiality(self):
        """Verify notes are stored safely in disha_case_notes and never exposed in Audit/Notification."""
        confidential_note = "Student discussed acute family distress and personal trauma."

        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="Confidentiality Test Case",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )

            # Transition with confidential notes
            await CaseService.transition_case_db(
                db=session,
                case_id=case.id,
                campus_id=self.campus_1,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                target_state_raw=CaseState.ASSIGNED.value,
                expected_version=1,
                new_owner_id=self.counsellor_id,
                due_at=utc_now() + timedelta(days=3),
                notes=confidential_note,
            )

            # 1. Verify note was saved in disha_case_notes
            note_res = await session.execute(
                select(CaseNote).where(CaseNote.case_id == case.id)
            )
            notes = note_res.scalars().all()
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0].content, confidential_note)

            # 2. Verify AuditEvent does NOT leak confidential note
            audit_res = await session.execute(
                select(AuditEvent).where(
                    AuditEvent.entity_id == case.id,
                    AuditEvent.action == "OWNER_ASSIGNED",
                )
            )
            audit = audit_res.scalar_one()
            audit_metadata = audit.event_metadata or {}
            self.assertNotIn("Student discussed acute family distress", str(audit_metadata))

            # 3. Verify Notification does NOT leak confidential note
            notif_res = await session.execute(
                select(NotificationOutbox).where(NotificationOutbox.case_id == case.id)
            )
            notif = notif_res.scalar_one()
            self.assertNotIn("Student discussed acute family distress", str(notif.safe_payload))

            # 4. Verify unauthorized role (e.g. Student) is forbidden from transitioning
            with self.assertRaises(PermissionDeniedError):
                await CaseService.transition_case_db(
                    db=session,
                    case_id=case.id,
                    campus_id=self.campus_1,
                    actor_user_id=self.student_user_id,
                    actor_roles=[Role.STUDENT.value],
                    target_state_raw=CaseState.ACCEPTED.value,
                    expected_version=2,
                )

    async def test_all_14_canonical_states_persistence(self):
        """Verify that all 14 canonical CaseState values persist and reload accurately."""
        all_states = [s for s in CaseState]
        self.assertEqual(len(all_states), 14)

        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_1,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_1_id,
                    title="14 States Iteration Case",
                    initial_state=CaseState.SUGGESTED.value,
                ),
            )

            for state in all_states:
                case.status = state.value
                await session.commit()

                # Reload in new query
                stmt = select(Case).where(Case.id == case.id)
                res = await session.execute(stmt)
                reloaded = res.scalar_one()

                self.assertEqual(reloaded.status, state.value)
                self.assertEqual(reloaded.state, state.value)
                self.assertIsInstance(reloaded.legacy_status, str)


if __name__ == "__main__":
    unittest.main()
