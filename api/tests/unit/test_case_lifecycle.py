import unittest
from datetime import timedelta
from app.shared.enums import CaseState, CaseStatus, map_status_to_state, map_state_to_status
from app.shared.utils import utc_now
from app.core.exceptions import (
    PermissionDeniedError,
    ConcurrencyConflictError,
    StateTransitionError,
)
from app.modules.cases.state_machine import CaseStateMachine, CANONICAL_TRANSITIONS
from app.modules.cases.services import CaseLifecycleService
from app.core.permissions import Role

class TestCaseLifecycleAndStateMachine(unittest.TestCase):

    def setUp(self):
        self.now = utc_now()
        self.campus_id = "campus-ipp-01"
        self.counsellor_id = "user-counsellor-01"
        self.admin_id = "user-admin-01"
        self.sample_case = {
            "id": "case-test-01",
            "campus_id": self.campus_id,
            "student_id": "student-001",
            "state": CaseState.ACTION_PLANNED.value,
            "status": CaseStatus.NEW.value,
            "priority": "high",
            "version": 1,
            "primary_owner_user_id": None,
            "due_at": self.now + timedelta(days=5),
            "created_at": self.now,
            "updated_at": self.now
        }

    # ==========================================
    # 1. COMPATIBILITY MAPPING TESTS
    # ==========================================

    def test_legacy_status_compatibility_mapping(self):
        """Verify legacy 6-status enums map seamlessly to canonical 14-state machine."""
        self.assertEqual(map_status_to_state("new"), CaseState.ACTION_PLANNED)
        self.assertEqual(map_status_to_state("assigned"), CaseState.ASSIGNED)
        self.assertEqual(map_status_to_state("in_progress"), CaseState.SUPPORT_IN_PROGRESS)
        self.assertEqual(map_status_to_state("resolved"), CaseState.OUTCOME_REVIEWED)
        self.assertEqual(map_status_to_state("closed"), CaseState.CLOSED)
        self.assertEqual(map_status_to_state("escalated"), CaseState.ASSIGNED)

    def test_canonical_state_to_legacy_status_mapping(self):
        """Verify canonical states project safely to legacy views."""
        self.assertEqual(map_state_to_status("action_planned"), CaseStatus.NEW)
        self.assertEqual(map_state_to_status("support_in_progress"), CaseStatus.IN_PROGRESS)
        self.assertEqual(map_state_to_status("outcome_reviewed"), CaseStatus.RESOLVED)
        self.assertEqual(map_state_to_status("closed"), CaseStatus.CLOSED)

    # ==========================================
    # 2. VALID STATE TRANSITION LIFECYCLE
    # ==========================================

    def test_complete_forward_lifecycle(self):
        """Test happy path from ACTION_PLANNED to CLOSED through support and outcome review."""
        case = dict(self.sample_case)

        # 1. ACTION_PLANNED -> ASSIGNED (Supervisor assigns counsellor)
        res1 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="assigned",
            expected_version=1,
            actor_user_id=self.admin_id,
            actor_roles=[Role.INSTITUTION_ADMIN.value],
            actor_campus_id=self.campus_id,
            new_owner_id=self.counsellor_id,
            due_at=self.now + timedelta(days=3)
        )
        self.assertEqual(res1["case"]["state"], CaseState.ASSIGNED.value)
        self.assertEqual(res1["case"]["version"], 2)
        self.assertEqual(res1["event"]["event_type"], "OWNER_ASSIGNED")
        self.assertIsNotNone(res1["notification_intent"])

        # 2. ASSIGNED -> ACCEPTED (Assigned counsellor accepts)
        res2 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="accepted",
            expected_version=2,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id
        )
        self.assertEqual(res2["case"]["state"], CaseState.ACCEPTED.value)
        self.assertEqual(res2["case"]["version"], 3)
        self.assertEqual(res2["event"]["event_type"], "ASSIGNMENT_ACCEPTED")

        # 3. ACCEPTED -> CONTACT_ATTEMPTED
        res3 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="contact_attempted",
            expected_version=3,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id
        )
        self.assertEqual(res3["case"]["state"], CaseState.CONTACT_ATTEMPTED.value)
        self.assertEqual(res3["case"]["version"], 4)

        # 4. CONTACT_ATTEMPTED -> SUPPORT_IN_PROGRESS
        res4 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="support_in_progress",
            expected_version=4,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id
        )
        self.assertEqual(res4["case"]["state"], CaseState.SUPPORT_IN_PROGRESS.value)
        self.assertEqual(res4["case"]["version"], 5)

        # 5. SUPPORT_IN_PROGRESS -> FOLLOW_UP_DUE (Requires follow-up check)
        res5 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="follow_up_due",
            expected_version=5,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id,
            has_follow_up=True
        )
        self.assertEqual(res5["case"]["state"], CaseState.FOLLOW_UP_DUE.value)
        self.assertEqual(res5["case"]["version"], 6)

        # 6. FOLLOW_UP_DUE -> OUTCOME_REVIEWED (Requires recorded outcome)
        res6 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="outcome_reviewed",
            expected_version=6,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id,
            has_outcome=True
        )
        self.assertEqual(res6["case"]["state"], CaseState.OUTCOME_REVIEWED.value)
        self.assertEqual(res6["case"]["version"], 7)

        # 7. OUTCOME_REVIEWED -> CLOSED (Requires note/reason)
        res7 = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="closed",
            expected_version=7,
            actor_user_id=self.counsellor_id,
            actor_roles=[Role.COUNSELLOR.value],
            actor_campus_id=self.campus_id,
            has_outcome=True,
            notes="Student attendance improved above threshold and academic guidance completed.",
            reason_code="GOALS_ACHIEVED"
        )
        self.assertEqual(res7["case"]["state"], CaseState.CLOSED.value)
        self.assertEqual(res7["case"]["version"], 8)
        self.assertIsNotNone(res7["case"]["closed_at"])

    # ==========================================
    # 3. REOPENING AND DISMISSAL
    # ==========================================

    def test_reopening_closed_case(self):
        """Verify closed cases can be formally reopened with explanatory note."""
        case = dict(self.sample_case)
        case["state"] = CaseState.CLOSED.value
        case["version"] = 10

        res = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="reopened",
            expected_version=10,
            actor_user_id=self.admin_id,
            actor_roles=[Role.INSTITUTION_ADMIN.value],
            actor_campus_id=self.campus_id,
            notes="New drop in attendance observed in semester 2",
            reason_code="NEW_SIGNAL_TRIGGERED"
        )
        self.assertEqual(res["case"]["state"], CaseState.REOPENED.value)
        self.assertEqual(res["case"]["version"], 11)

    def test_dismissal_from_under_review(self):
        """Verify early dismissal requires mandatory reason code/note."""
        case = dict(self.sample_case)
        case["state"] = CaseState.UNDER_REVIEW.value
        case["version"] = 2

        # Missing reason code/note should fail guard check
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="dismissed",
                expected_version=2,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id=self.campus_id,
                notes=None
            )

        # Providing mandatory rationale succeeds
        res = CaseLifecycleService.transition_case(
            case=case,
            target_state_raw="dismissed",
            expected_version=2,
            actor_user_id=self.admin_id,
            actor_roles=[Role.INSTITUTION_ADMIN.value],
            actor_campus_id=self.campus_id,
            notes="Approved medical leave on file; false positive absence spike",
            reason_code="EXCUSED_MEDICAL_LEAVE"
        )
        self.assertEqual(res["case"]["state"], CaseState.DISMISSED.value)
        self.assertIsNotNone(res["case"]["closed_at"])

    # ==========================================
    # 4. GUARDS AND ERROR PREVENTION
    # ==========================================

    def test_invalid_arbitrary_transition_rejected(self):
        """Prevent arbitrary jumps such as ACTION_PLANNED -> CLOSED."""
        case = dict(self.sample_case)
        case["state"] = CaseState.ACTION_PLANNED.value
        with self.assertRaises(StateTransitionError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="closed",
                expected_version=1,
                actor_user_id=self.counsellor_id,
                actor_roles=[Role.COUNSELLOR.value],
                actor_campus_id=self.campus_id
            )

    def test_unauthorized_role_rejected(self):
        """Faculty or Student cannot transition case to ACCEPTED or CLOSED."""
        case = dict(self.sample_case)
        case["state"] = CaseState.ASSIGNED.value
        with self.assertRaises(PermissionDeniedError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="accepted",
                expected_version=1,
                actor_user_id="user-faculty-01",
                actor_roles=[Role.FACULTY.value],
                actor_campus_id=self.campus_id
            )

    def test_unassigned_counsellor_cannot_accept(self):
        """Only the designated owner or admin can accept the case."""
        case = dict(self.sample_case)
        case["state"] = CaseState.ASSIGNED.value
        case["primary_owner_user_id"] = "user-counsellor-01"

        with self.assertRaises(PermissionDeniedError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="accepted",
                expected_version=1,
                actor_user_id="user-counsellor-02", # Different counsellor
                actor_roles=[Role.COUNSELLOR.value],
                actor_campus_id=self.campus_id
            )

    def test_optimistic_concurrency_conflict(self):
        """Version mismatch must throw ConcurrencyConflictError (HTTP 409)."""
        case = dict(self.sample_case)
        case["version"] = 5
        with self.assertRaises(ConcurrencyConflictError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="assigned",
                expected_version=4, # Stale version
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id=self.campus_id
            )

    def test_cross_campus_isolation(self):
        """Actor from another campus cannot mutate case."""
        case = dict(self.sample_case)
        with self.assertRaises(PermissionDeniedError):
            CaseLifecycleService.transition_case(
                case=case,
                target_state_raw="assigned",
                expected_version=1,
                actor_user_id="user-foreign-admin",
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                actor_campus_id="campus-other-99"
            )

