from typing import Dict, Set
from app.shared.enums import CaseState
from app.core.exceptions import StateTransitionError

# Canonical DISHA case lifecycle transition graph
PERMITTED_TRANSITIONS: Dict[str, Set[str]] = {
    CaseState.SUGGESTED.value: {
        CaseState.UNDER_REVIEW.value,
        CaseState.DISMISSED.value
    },
    CaseState.UNDER_REVIEW.value: {
        CaseState.ACTION_PLANNED.value,
        CaseState.DISMISSED.value
    },
    CaseState.ACTION_PLANNED.value: {
        CaseState.ASSIGNED.value,
        CaseState.DISMISSED.value
    },
    CaseState.ASSIGNED.value: {
        CaseState.ACCEPTED.value,
        CaseState.ACTION_PLANNED.value,
        CaseState.DISMISSED.value
    },
    CaseState.ACCEPTED.value: {
        CaseState.CONTACT_ATTEMPTED.value,
        CaseState.SUPPORT_IN_PROGRESS.value,
        CaseState.FAILED_CONTACT.value,
        CaseState.ASSIGNED.value # Re-delegation
    },
    CaseState.CONTACT_ATTEMPTED.value: {
        CaseState.SUPPORT_IN_PROGRESS.value,
        CaseState.FAILED_CONTACT.value,
        CaseState.FOLLOW_UP_DUE.value
    },
    CaseState.FAILED_CONTACT.value: {
        CaseState.CONTACT_ATTEMPTED.value,
        CaseState.CLOSED.value,
        CaseState.DISMISSED.value
    },
    CaseState.SUPPORT_IN_PROGRESS.value: {
        CaseState.FOLLOW_UP_DUE.value,
        CaseState.OUTCOME_REVIEWED.value,
        CaseState.SERVICE_UNAVAILABLE.value
    },
    CaseState.FOLLOW_UP_DUE.value: {
        CaseState.SUPPORT_IN_PROGRESS.value,
        CaseState.OUTCOME_REVIEWED.value,
        CaseState.FAILED_CONTACT.value
    },
    CaseState.SERVICE_UNAVAILABLE.value: {
        CaseState.ACTION_PLANNED.value,
        CaseState.CLOSED.value
    },
    CaseState.OUTCOME_REVIEWED.value: {
        CaseState.CLOSED.value,
        CaseState.SUPPORT_IN_PROGRESS.value
    },
    CaseState.CLOSED.value: {
        CaseState.REOPENED.value
    },
    CaseState.REOPENED.value: {
        CaseState.ASSIGNED.value,
        CaseState.ACCEPTED.value,
        CaseState.UNDER_REVIEW.value
    },
    CaseState.DISMISSED.value: {
        CaseState.REOPENED.value
    }
}

def validate_case_transition(from_state: str, to_state: str) -> None:
    """Enforce strict lifecycle transitions without arbitrary jumping."""
    if from_state == to_state:
        return
        
    allowed_targets = PERMITTED_TRANSITIONS.get(from_state, set())
    if to_state not in allowed_targets:
        raise StateTransitionError(
            from_state=from_state,
            to_state=to_state,
            reason=f"Permitted next states from '{from_state}' are: {sorted(list(allowed_targets))}"
        )
