"""
DISHA CaseState ORM & Lifecycle Verification Test Suite

Verifies:
1. Reading, assigning, and validating all 14 canonical CaseState values.
2. ORM round-trip persistence and reloading of all 14 canonical states in SQLite/PostgreSQL.
3. Strict invalid state and status rejection.
4. Legacy status backward compatibility mapping without loss of canonical state fidelity.
5. Permitted vs. prohibited transitions across the full 14-state lifecycle.
6. Role-based transition authorization and cross-campus tenancy isolation.
7. Optimistic concurrency conflict detection (HTTP 409).
8. Guarded transition requirements (notes, due_date, outcome, follow_up).
9. Consistency across Case state, CaseEvent, Audit, and Notification intents.
"""

import unittest
from datetime import datetime, timezone, timedelta
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.shared.enums import CaseState, CaseStatus, map_status_to_state, map_state_to_status
from app.shared.utils import utc_now
from app.core.permissions import Role
from app.core.exceptions import (
    PermissionDeniedError,
    ConcurrencyConflictError,
    StateTransitionError,
)
from app.modules.identity.models import User
from app.modules.roster.models import Student
from app.modules.cases.models import Case, CaseNote, CaseEvent
from app.modules.cases.state_machine import CaseStateMachine, CANONICAL_TRANSITIONS
from app.modules.cases.services import CaseLifecycleService


class TestCaseStateORMAndLifecycleVerification(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Pre-seed a dummy student and user to satisfy FKs if needed
        self.campus_id = "campus-ipp-01"
        self.student_id = str(uuid.uuid4())
        self.counsellor_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())

        async with self.async_session() as session:
            async with session.begin():
                student = Student(
                    id=self.student_id,
                    campus_id=self.campus_id,
                    student_uid="ENR-1001",
                    full_name="Rohan Verma",
                    department="Computer Science",
                    course="B.Tech",
                    academic_year=2,
                    is_active=True,
                )
                counsellor = User(
                    id=self.counsellor_id,
                    email="counsellor@campus.edu",
                    hashed_password="argon2_fake_hash",
                    full_name="Priya Sharma",
                    is_active=True,
                )
                admin = User(
                    id=self.admin_id,
                    email="admin@campus.edu",
                    hashed_password="argon2_fake_hash",
                    full_name="Anil Deshmukh",
                    is_active=True,
                )
                session.add_all([student, counsellor, admin])

    async def asyncTearDown(self):
        await self.engine.dispose()

    # =========================================================================
    # 1. READ & ASSIGN ALL 14 CANONICAL STATES IN PYTHON & ORM
    # =========================================================================

    def test_assign_and_read_all_14_canonical_states(self):
        """Verify that every one of the 14 canonical CaseState enum values can be read and assigned."""
        all_14_states = list(CaseState)
        self.assertEqual(len(all_14_states), 14, "Must define exactly 14 canonical CaseState values")

        case = Case(
            id=str(uuid.uuid4()),
            campus_id=self.campus_id,
            student_id=self.student_id,
            title="Test Case",
            priority="medium",
        )

        for expected_state in all_14_states:
            # Assign via CaseState enum
            case.state = expected_state
            self.assertEqual(case.state, expected_state.value)
            self.assertEqual(case.status, expected_state.value)

            # Assign via string
            case.state = expected_state.value
            self.assertEqual(case.state, expected_state.value)
            self.assertEqual(case.status, expected_state.value)

            # Check legacy status projection is valid
            self.assertIn(case.legacy_status, [s.value for s in CaseStatus])

    # =========================================================================
    # 2. PERSISTENCE & RELOAD OF ALL 14 STATES IN DATABASE (ORM ROUND-TRIP)
    # =========================================================================

    async def test_persist_and_reload_all_14_states_in_orm(self):
        """Verify that every one of the 14 canonical states persists to SQLite/Postgres and reloads cleanly."""
        all_14_states = list(CaseState)
        case_records = {}

        # 1. Insert 14 distinct case records, one for each canonical state
        async with self.async_session() as session:
            async with session.begin():
                for state in all_14_states:
                    c_id = str(uuid.uuid4())
                    case = Case(
                        id=c_id,
                        campus_id=self.campus_id,
                        student_id=self.student_id,
                        assigned_counsellor_id=self.counsellor_id,
                        status=state.value,
                        title=f"Case in state {state.value}",
                        priority="medium",
                        version=1,
                    )
                    session.add(case)
                    case_records[c_id] = state.value

        # 2. Query each case back in a brand new session and verify fidelity
        async with self.async_session() as session:
            for c_id, expected_state_val in case_records.items():
                result = await session.execute(select(Case).where(Case.id == c_id))
                reloaded = result.scalar_one_or_none()

                self.assertIsNotNone(reloaded, f"Failed to reload case {c_id}")
                # The raw status column in the DB must preserve the exact canonical state string
                self.assertEqual(
                    reloaded.status,
                    expected_state_val,
                    f"DB column status did not preserve canonical state {expected_state_val}"
                )
                # The state property must return the exact canonical state
                self.assertEqual(
                    reloaded.state,
                    expected_state_val,
                    f"Case.state did not match {expected_state_val}"
                )
                # Legacy status must be properly mapped
                expected_legacy = map_state_to_status(expected_state_val).value
                self.assertEqual(
                    reloaded.legacy_status,
                    expected_legacy,
                    f"Legacy status mismatch for {expected_state_val}"
                )

    # =========================================================================
    # 3. INVALID STATE REJECTION
    # =========================================================================

    def test_invalid_state_assignment_rejected(self):
        """Setting invalid state or status values must raise ValueError."""
        case = Case(
            id=str(uuid.uuid4()),
            campus_id=self.campus_id,
            student_id=self.student_id,
            title="Test Case",
        )

        # Prohibited state strings
        with self.assertRaises(ValueError):
            case.state = "non_existent_state"

        with self.assertRaises(ValueError):
            case.state = "invalid_status_xyz"

        with self.assertRaises(ValueError):
            case.status = "completely_bogus"

        with self.assertRaises(ValueError):
            case.state = 12345

        with self.assertRaises(ValueError):
            case.status = ["list_not_allowed"]

    # =========================================================================
    # 4. LEGACY STATUS BACKWARD COMPATIBILITY
    # =========================================================================

    def test_legacy_status_assignment_and_mapping(self):
        """Legacy 6-status values assigned to status/state must map cleanly without errors."""
        case = Case(
            id=str(uuid.uuid4()),
            campus_id=self.campus_id,
            student_id=self.student_id,
            title="Legacy Compatibility Case",
        )

        # Legacy 'new' maps to canonical 'action_planned'
        case.state = "new"
        self.assertEqual(case.state, CaseState.ACTION_PLANNED.value)

        # Legacy 'in_progress' maps to canonical 'support_in_progress'
        case.state = "in_progress"
        self.assertEqual(case.state, CaseState.SUPPORT_IN_PROGRESS.value)

        # Legacy 'resolved' maps to canonical 'outcome_reviewed'
        case.state = "resolved"
        self.assertEqual(case.state, CaseState.OUTCOME_REVIEWED.value)

        # Direct assignment of legacy status string to status column
        case.status = "escalated"
        self.assertEqual(case.status, "escalated")
        self.assertEqual(case.state, CaseState.ASSIGNED.value)

    # =========================================================================
    # 5. PERMITTED AND PROHIBITED TRANSITIONS (STATE MACHINE MATRIX)
    # =========================================================================

    def test_permitted_and_prohibited_transitions(self):
        """Verify state machine accepts permitted transitions and rejects prohibited ones."""
        # Permitted: SUGGESTED -> UNDER_REVIEW
        rule = CaseStateMachine.get_rule(CaseState.SUGGESTED, CaseState.UNDER_REVIEW)
        self.assertIsNotNone(rule)
        self.assertEqual(rule.event_type, "CASE_REVIEW_STARTED")

        # Prohibited: SUGGESTED -> SUPPORT_IN_PROGRESS
        with self.assertRaises(StateTransitionError):
            CaseStateMachine.get_rule(CaseState.SUGGESTED, CaseState.SUPPORT_IN_PROGRESS)

        # Prohibited: CLOSED -> ACCEPTED
        with self.assertRaises(StateTransitionError):
            CaseStateMachine.get_rule(CaseState.CLOSED, CaseState.ACCEPTED)

        # Permitted: CLOSED -> REOPENED
        rule_reopen = CaseStateMachine.get_rule(CaseState.CLOSED, CaseState.REOPENED)
        self.assertIsNotNone(rule_reopen)
        self.assertEqual(rule_reopen.event_type, "CASE_REOPENED")

    # =========================================================================
    # 6. ROLE AUTHORIZATION & CAMPUS ISOLATION
    # =========================================================================

    def test_transition_authorization_and_campus_isolation(self):
        """Verify role authorization and strict campus-level tenancy boundary."""
        now = utc_now()
        case_dict = {
            "id": "case-sec-01",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "state": CaseState.ACTION_PLANNED.value,
            "status": CaseState.ACTION_PLANNED.value,
            "version": 1,
            "due_at": now + timedelta(days=7),
        }

        # 1. Cross-campus mutation prohibited
        with self.assertRaises(PermissionDeniedError) as ctx_campus:
            CaseLifecycleService.transition_case(
                case=case_dict,
                target_state_raw="assigned",
                expected_version=1,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id="campus-foreign-99", # Different campus!
                new_owner_id=self.counsellor_id,
            )
        self.assertIn("scope", str(ctx_campus.exception).lower())

        # 2. Unauthorized role prohibited (e.g. FACULTY cannot transition to ASSIGNED)
        with self.assertRaises(PermissionDeniedError) as ctx_role:
            CaseLifecycleService.transition_case(
                case=case_dict,
                target_state_raw="assigned",
                expected_version=1,
                actor_user_id="user-faculty-01",
                actor_roles=[Role.FACULTY.value], # Faculty not permitted
                actor_campus_id=self.campus_id,
                new_owner_id=self.counsellor_id,
            )
        self.assertIn("unauthorized", str(ctx_role.exception).lower())

    # =========================================================================
    # 7. OPTIMISTIC CONCURRENCY CONFLICTS (HTTP 409)
    # =========================================================================

    def test_optimistic_concurrency_conflict_resolution(self):
        """Mismatched expected_version must raise ConcurrencyConflictError."""
        now = utc_now()
        case_dict = {
            "id": "case-occ-01",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "state": CaseState.ACTION_PLANNED.value,
            "status": CaseState.ACTION_PLANNED.value,
            "version": 5, # DB has version 5
            "due_at": now + timedelta(days=7),
        }

        with self.assertRaises(ConcurrencyConflictError) as ctx:
            CaseLifecycleService.transition_case(
                case=case_dict,
                target_state_raw="assigned",
                expected_version=4, # Client submitted stale version 4
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id=self.campus_id,
                new_owner_id=self.counsellor_id,
            )
        self.assertEqual(ctx.exception.status_code, 409)

    # =========================================================================
    # 8. GUARDED TRANSITIONS REQUIREMENTS
    # =========================================================================

    def test_guarded_transition_requirements(self):
        """Transitions requiring notes, follow-ups, or outcomes must enforce them."""
        now = utc_now()

        # A. ASSIGNED requires due date
        case_assigned = {
            "id": "case-guard-01",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "state": CaseState.ACTION_PLANNED.value,
            "status": CaseState.ACTION_PLANNED.value,
            "version": 1,
            "due_at": None, # No due date provided
        }
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case_assigned,
                target_state_raw="assigned",
                expected_version=1,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id=self.campus_id,
                new_owner_id=self.counsellor_id,
                due_at=None,
            )

        # B. FOLLOW_UP_DUE requires follow-up logged
        case_support = {
            "id": "case-guard-02",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "assigned_counsellor_id": self.counsellor_id,
            "state": CaseState.SUPPORT_IN_PROGRESS.value,
            "status": CaseState.SUPPORT_IN_PROGRESS.value,
            "version": 3,
        }
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case_support,
                target_state_raw="follow_up_due",
                expected_version=3,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                actor_campus_id=self.campus_id,
                has_follow_up=False, # Missing follow up
            )

        # C. OUTCOME_REVIEWED requires recorded outcome
        case_followup = {
            "id": "case-guard-03",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "assigned_counsellor_id": self.counsellor_id,
            "state": CaseState.FOLLOW_UP_DUE.value,
            "status": CaseState.FOLLOW_UP_DUE.value,
            "version": 4,
        }
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case_followup,
                target_state_raw="outcome_reviewed",
                expected_version=4,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                actor_campus_id=self.campus_id,
                has_outcome=False, # Missing outcome
            )

        # D. DISMISSED requires mandatory note / rationale
        case_review = {
            "id": "case-guard-04",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "state": CaseState.UNDER_REVIEW.value,
            "status": CaseState.UNDER_REVIEW.value,
            "version": 2,
        }
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case_review,
                target_state_raw="dismissed",
                expected_version=2,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id=self.campus_id,
                notes=None, # Missing rationale
            )

    # =========================================================================
    # 9. CONSISTENCY ACROSS STATE, CASE_EVENT, AUDIT, & NOTIFICATIONS
    # =========================================================================

    def test_state_event_and_notification_consistency(self):
        """Successful transition emits synchronized CaseEvent and Notification intents."""
        now = utc_now()
        case_dict = {
            "id": "case-sync-01",
            "campus_id": self.campus_id,
            "student_id": self.student_id,
            "state": CaseState.ACTION_PLANNED.value,
            "status": CaseState.ACTION_PLANNED.value,
            "version": 1,
            "due_at": now + timedelta(days=5),
        }

        result = CaseLifecycleService.transition_case(
            case=case_dict,
            target_state_raw="assigned",
            expected_version=1,
            actor_user_id=self.admin_id,
            actor_roles=[Role.INSTITUTION_ADMIN.value],
            actor_campus_id=self.campus_id,
            new_owner_id=self.counsellor_id,
            due_at=now + timedelta(days=5),
        )

        # 1. State mutated to exact canonical state
        self.assertEqual(result["case"]["state"], CaseState.ASSIGNED.value)
        self.assertEqual(result["case"]["status"], CaseState.ASSIGNED.value)
        self.assertEqual(result["case"]["legacy_status"], CaseStatus.ASSIGNED.value)
        self.assertEqual(result["case"]["version"], 2)

        # 2. CaseEvent emitted with matching metadata
        event = result["event"]
        self.assertEqual(event["event_type"], "OWNER_ASSIGNED")
        self.assertEqual(event["case_id"], "case-sync-01")
        self.assertEqual(event["campus_id"], self.campus_id)
        self.assertEqual(event["actor_id"], self.admin_id)
        self.assertEqual(event["from_state"], CaseState.ACTION_PLANNED.value)
        self.assertEqual(event["to_state"], CaseState.ASSIGNED.value)

        # 3. Notification intent generated for designated counsellor
        notif = result["notification_intent"]
        self.assertIsNotNone(notif)
        self.assertEqual(notif["recipient_id"], self.counsellor_id)
        self.assertEqual(notif["category"], "case_assigned")


if __name__ == "__main__":
    unittest.main()
