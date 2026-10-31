from enum import Enum
from typing import Dict

class CaseState(str, Enum):
    """Canonical 14-state lifecycle as specified in Blueprint 07."""
    SUGGESTED = "suggested"
    UNDER_REVIEW = "under_review"
    ACTION_PLANNED = "action_planned"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    CONTACT_ATTEMPTED = "contact_attempted"
    SUPPORT_IN_PROGRESS = "support_in_progress"
    FAILED_CONTACT = "failed_contact"
    FOLLOW_UP_DUE = "follow_up_due"
    SERVICE_UNAVAILABLE = "service_unavailable"
    OUTCOME_REVIEWED = "outcome_reviewed"
    CLOSED = "closed"
    REOPENED = "reopened"
    DISMISSED = "dismissed"

class CaseStatus(str, Enum):
    """Legacy 6-state enumeration preserved for backward compatibility."""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"

# Bi-directional compatibility mappings
STATUS_TO_STATE_MAP: Dict[str, CaseState] = {
    CaseStatus.NEW.value: CaseState.ACTION_PLANNED,
    CaseStatus.ASSIGNED.value: CaseState.ASSIGNED,
    CaseStatus.IN_PROGRESS.value: CaseState.SUPPORT_IN_PROGRESS,
    CaseStatus.ESCALATED.value: CaseState.ASSIGNED, # Escalation is tracked via is_escalated flag
    CaseStatus.RESOLVED.value: CaseState.OUTCOME_REVIEWED,
    CaseStatus.CLOSED.value: CaseState.CLOSED,
}

STATE_TO_STATUS_MAP: Dict[str, CaseStatus] = {
    CaseState.SUGGESTED.value: CaseStatus.NEW,
    CaseState.UNDER_REVIEW.value: CaseStatus.NEW,
    CaseState.ACTION_PLANNED.value: CaseStatus.NEW,
    CaseState.ASSIGNED.value: CaseStatus.ASSIGNED,
    CaseState.ACCEPTED.value: CaseStatus.ASSIGNED,
    CaseState.CONTACT_ATTEMPTED.value: CaseStatus.IN_PROGRESS,
    CaseState.SUPPORT_IN_PROGRESS.value: CaseStatus.IN_PROGRESS,
    CaseState.FAILED_CONTACT.value: CaseStatus.IN_PROGRESS,
    CaseState.FOLLOW_UP_DUE.value: CaseStatus.IN_PROGRESS,
    CaseState.SERVICE_UNAVAILABLE.value: CaseStatus.IN_PROGRESS,
    CaseState.OUTCOME_REVIEWED.value: CaseStatus.RESOLVED,
    CaseState.CLOSED.value: CaseStatus.CLOSED,
    CaseState.REOPENED.value: CaseStatus.ASSIGNED,
    CaseState.DISMISSED.value: CaseStatus.CLOSED,
}

def map_status_to_state(status: str) -> CaseState:
    """Safely map legacy or string status to canonical CaseState."""
    status_lower = str(status).lower()
    if status_lower in [s.value for s in CaseState]:
        return CaseState(status_lower)
    return STATUS_TO_STATE_MAP.get(status_lower, CaseState.ACTION_PLANNED)

def map_state_to_status(state: str) -> CaseStatus:
    """Safely map canonical CaseState to legacy CaseStatus."""
    state_lower = str(state).lower()
    if state_lower in [s.value for s in CaseStatus]:
        return CaseStatus(state_lower)
    return STATE_TO_STATUS_MAP.get(state_lower, CaseStatus.IN_PROGRESS)

class SignalResult(str, Enum):
    ATTENTION_SUGGESTED = "attention_suggested"
    NO_RULE_TRIGGERED = "no_rule_triggered"
    UNKNOWN = "unknown"

class ObservationDomain(str, Enum):
    ATTENDANCE = "attendance"
    ACADEMIC = "academic"
    PARTICIPATION = "participation"
    SKILLS = "skills"
    FACULTY_FEEDBACK = "faculty_feedback"
    FEE_STATUS = "fee_status"
