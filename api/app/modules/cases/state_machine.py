from typing import Dict, Set, Optional, List
from pydantic import BaseModel
from app.shared.enums import CaseState
from app.core.permissions import Role
from app.core.exceptions import StateTransitionError, PermissionDeniedError

class TransitionRule(BaseModel):
    from_state: CaseState
    to_state: CaseState
    event_type: str
    allowed_roles: List[Role]
    requires_assigned_owner: bool = False
    requires_due_date: bool = False
    requires_case_note: bool = False
    requires_follow_up: bool = False
    requires_outcome: bool = False
    is_terminal: bool = False
    generates_audit: bool = True
    generates_notification: bool = True

# Canonical 14-state transition table conforming to Blueprint 07 §1
CANONICAL_TRANSITIONS: Dict[CaseState, Dict[CaseState, TransitionRule]] = {
    CaseState.SUGGESTED: {
        CaseState.UNDER_REVIEW: TransitionRule(
            from_state=CaseState.SUGGESTED,
            to_state=CaseState.UNDER_REVIEW,
            event_type="CASE_REVIEW_STARTED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.HOD, Role.PLATFORM_ADMIN],
            requires_assigned_owner=False
        ),
        CaseState.DISMISSED: TransitionRule(
            from_state=CaseState.SUGGESTED,
            to_state=CaseState.DISMISSED,
            event_type="SIGNAL_DISMISSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.UNDER_REVIEW: {
        CaseState.ACTION_PLANNED: TransitionRule(
            from_state=CaseState.UNDER_REVIEW,
            to_state=CaseState.ACTION_PLANNED,
            event_type="INTERVENTION_APPROVED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.HOD, Role.PLATFORM_ADMIN]
        ),
        CaseState.DISMISSED: TransitionRule(
            from_state=CaseState.UNDER_REVIEW,
            to_state=CaseState.DISMISSED,
            event_type="SIGNAL_DISMISSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.ACTION_PLANNED: {
        CaseState.ASSIGNED: TransitionRule(
            from_state=CaseState.ACTION_PLANNED,
            to_state=CaseState.ASSIGNED,
            event_type="OWNER_ASSIGNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.COUNSELLOR, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_due_date=True
        ),
        CaseState.DISMISSED: TransitionRule(
            from_state=CaseState.ACTION_PLANNED,
            to_state=CaseState.DISMISSED,
            event_type="SIGNAL_DISMISSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.ASSIGNED: {
        CaseState.ACCEPTED: TransitionRule(
            from_state=CaseState.ASSIGNED,
            to_state=CaseState.ACCEPTED,
            event_type="ASSIGNMENT_ACCEPTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.ASSIGNED: TransitionRule(
            from_state=CaseState.ASSIGNED,
            to_state=CaseState.ASSIGNED,
            event_type="OWNER_REASSIGNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
        CaseState.ACTION_PLANNED: TransitionRule(
            from_state=CaseState.ASSIGNED,
            to_state=CaseState.ACTION_PLANNED,
            event_type="ASSIGNMENT_REJECTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_case_note=True
        ),
        CaseState.DISMISSED: TransitionRule(
            from_state=CaseState.ASSIGNED,
            to_state=CaseState.DISMISSED,
            event_type="CASE_DISMISSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.ACCEPTED: {
        CaseState.CONTACT_ATTEMPTED: TransitionRule(
            from_state=CaseState.ACCEPTED,
            to_state=CaseState.CONTACT_ATTEMPTED,
            event_type="CONTACT_ATTEMPTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.SUPPORT_IN_PROGRESS: TransitionRule(
            from_state=CaseState.ACCEPTED,
            to_state=CaseState.SUPPORT_IN_PROGRESS,
            event_type="SUPPORT_STARTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.FAILED_CONTACT: TransitionRule(
            from_state=CaseState.ACCEPTED,
            to_state=CaseState.FAILED_CONTACT,
            event_type="CONTACT_FAILED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
        CaseState.ASSIGNED: TransitionRule(
            from_state=CaseState.ACCEPTED,
            to_state=CaseState.ASSIGNED,
            event_type="OWNER_REASSIGNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
    },
    CaseState.CONTACT_ATTEMPTED: {
        CaseState.SUPPORT_IN_PROGRESS: TransitionRule(
            from_state=CaseState.CONTACT_ATTEMPTED,
            to_state=CaseState.SUPPORT_IN_PROGRESS,
            event_type="SUPPORT_STARTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.FAILED_CONTACT: TransitionRule(
            from_state=CaseState.CONTACT_ATTEMPTED,
            to_state=CaseState.FAILED_CONTACT,
            event_type="CONTACT_FAILED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
        CaseState.FOLLOW_UP_DUE: TransitionRule(
            from_state=CaseState.CONTACT_ATTEMPTED,
            to_state=CaseState.FOLLOW_UP_DUE,
            event_type="FOLLOW_UP_SCHEDULED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_follow_up=True
        ),
    },
    CaseState.FAILED_CONTACT: {
        CaseState.CONTACT_ATTEMPTED: TransitionRule(
            from_state=CaseState.FAILED_CONTACT,
            to_state=CaseState.CONTACT_ATTEMPTED,
            event_type="CONTACT_REATTEMPTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.CLOSED: TransitionRule(
            from_state=CaseState.FAILED_CONTACT,
            to_state=CaseState.CLOSED,
            event_type="CASE_CLOSED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
        CaseState.DISMISSED: TransitionRule(
            from_state=CaseState.FAILED_CONTACT,
            to_state=CaseState.DISMISSED,
            event_type="CASE_DISMISSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.SUPPORT_IN_PROGRESS: {
        CaseState.FOLLOW_UP_DUE: TransitionRule(
            from_state=CaseState.SUPPORT_IN_PROGRESS,
            to_state=CaseState.FOLLOW_UP_DUE,
            event_type="SUPPORT_DELIVERED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_follow_up=True
        ),
        CaseState.OUTCOME_REVIEWED: TransitionRule(
            from_state=CaseState.SUPPORT_IN_PROGRESS,
            to_state=CaseState.OUTCOME_REVIEWED,
            event_type="OUTCOME_RECORDED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_outcome=True
        ),
        CaseState.SERVICE_UNAVAILABLE: TransitionRule(
            from_state=CaseState.SUPPORT_IN_PROGRESS,
            to_state=CaseState.SERVICE_UNAVAILABLE,
            event_type="SERVICE_UNAVAILABLE",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
    },
    CaseState.FOLLOW_UP_DUE: {
        CaseState.SUPPORT_IN_PROGRESS: TransitionRule(
            from_state=CaseState.FOLLOW_UP_DUE,
            to_state=CaseState.SUPPORT_IN_PROGRESS,
            event_type="SUPPORT_RESUMED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.OUTCOME_REVIEWED: TransitionRule(
            from_state=CaseState.FOLLOW_UP_DUE,
            to_state=CaseState.OUTCOME_REVIEWED,
            event_type="OUTCOME_RECORDED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_outcome=True
        ),
        CaseState.FAILED_CONTACT: TransitionRule(
            from_state=CaseState.FOLLOW_UP_DUE,
            to_state=CaseState.FAILED_CONTACT,
            event_type="CONTACT_FAILED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True,
            requires_case_note=True
        ),
    },
    CaseState.SERVICE_UNAVAILABLE: {
        CaseState.ACTION_PLANNED: TransitionRule(
            from_state=CaseState.SERVICE_UNAVAILABLE,
            to_state=CaseState.ACTION_PLANNED,
            event_type="ALTERNATIVE_INTERVENTION_PLANNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.PLATFORM_ADMIN],
            requires_case_note=True
        ),
        CaseState.CLOSED: TransitionRule(
            from_state=CaseState.SERVICE_UNAVAILABLE,
            to_state=CaseState.CLOSED,
            event_type="CASE_CLOSED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.PLATFORM_ADMIN],
            requires_case_note=True,
            is_terminal=True
        ),
    },
    CaseState.OUTCOME_REVIEWED: {
        CaseState.CLOSED: TransitionRule(
            from_state=CaseState.OUTCOME_REVIEWED,
            to_state=CaseState.CLOSED,
            event_type="CASE_CLOSED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_outcome=True,
            requires_case_note=True,
            is_terminal=True
        ),
        CaseState.SUPPORT_IN_PROGRESS: TransitionRule(
            from_state=CaseState.OUTCOME_REVIEWED,
            to_state=CaseState.SUPPORT_IN_PROGRESS,
            event_type="FURTHER_SUPPORT_REQUESTED",
            allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN],
            requires_case_note=True
        ),
    },
    CaseState.CLOSED: {
        CaseState.REOPENED: TransitionRule(
            from_state=CaseState.CLOSED,
            to_state=CaseState.REOPENED,
            event_type="CASE_REOPENED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.PLATFORM_ADMIN],
            requires_case_note=True
        ),
    },
    CaseState.REOPENED: {
        CaseState.ASSIGNED: TransitionRule(
            from_state=CaseState.REOPENED,
            to_state=CaseState.ASSIGNED,
            event_type="OWNER_ASSIGNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.PLATFORM_ADMIN],
            requires_assigned_owner=True
        ),
        CaseState.ACTION_PLANNED: TransitionRule(
            from_state=CaseState.REOPENED,
            to_state=CaseState.ACTION_PLANNED,
            event_type="INTERVENTION_REPLANNED",
            allowed_roles=[Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.PLATFORM_ADMIN]
        ),
    },
    CaseState.DISMISSED: {
        # Blueprint 07 §1.2 CASE-SM-08: dismissed is terminal (cannot be reopened without explicit administrative override)
    }
}

class CaseStateMachine:
    """Centralized lifecycle validator ensuring deterministic state transitions and guard validation."""

    @staticmethod
    def get_rule(from_state: CaseState, to_state: CaseState) -> TransitionRule:
        targets = CANONICAL_TRANSITIONS.get(from_state, {})
        rule = targets.get(to_state)
        if not rule:
            permitted = [s.value for s in targets.keys()]
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason=f"Permitted next states from '{from_state.value}' are: {permitted}"
            )
        return rule

    @staticmethod
    def validate_transition(
        from_state: CaseState,
        to_state: CaseState,
        actor_roles: List[str],
        actor_user_id: str,
        owner_user_id: Optional[str],
        has_due_date: bool = True,
        has_case_note: bool = False,
        has_follow_up: bool = False,
        has_outcome: bool = False,
        is_override: bool = False
    ) -> TransitionRule:
        # Same state transition: no-op idempotent check
        if from_state == to_state:
            # Special case: reassignment while remaining in ASSIGNED
            if from_state == CaseState.ASSIGNED and to_state == CaseState.ASSIGNED:
                pass
            else:
                return TransitionRule(
                    from_state=from_state,
                    to_state=to_state,
                    event_type="CASE_UNCHANGED",
                    allowed_roles=[Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN]
                )

        rule = CaseStateMachine.get_rule(from_state, to_state)

        # 1. Role validation
        role_enums = [r.value for r in rule.allowed_roles]
        if not any(r in role_enums for r in actor_roles) and Role.PLATFORM_ADMIN.value not in actor_roles:
            raise PermissionDeniedError(
                f"Role unauthorized for transition {from_state.value} -> {to_state.value}. Requires one of: {role_enums}"
            )

        # 2. Ownership guard: actions like ACCEPTED, CONTACT_ATTEMPTED, etc. require assigned owner
        is_admin = any(r in [Role.INSTITUTION_ADMIN.value, Role.PLATFORM_ADMIN.value] for r in actor_roles)
        if rule.requires_assigned_owner and not is_admin:
            if not owner_user_id or owner_user_id != actor_user_id:
                raise PermissionDeniedError(
                    f"Only the designated primary owner can perform transition to '{to_state.value}'"
                )

        # 3. Guard: requires due_date
        if rule.requires_due_date and not has_due_date:
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason="Transition requires an active due date (SLA deadline)"
            )

        # 4. Guard: requires case note / explanation
        if rule.requires_case_note and not has_case_note:
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason="Mandatory explanatory note or reason code required for this state transition"
            )

        # 5. Guard: requires follow-up
        if rule.requires_follow_up and not has_follow_up:
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason="At least one logged follow-up record is required before entering this state"
            )

        # 6. Guard: requires recorded outcome
        if rule.requires_outcome and not has_outcome:
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason="A recorded case outcome evaluation is required before entering this state"
            )

        return rule

