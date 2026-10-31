from enum import Enum

class CaseStatus(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"

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
