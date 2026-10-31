from enum import Enum
from typing import Dict


class CaseState(str, Enum):
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
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CasePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FollowUpStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    MISSED = "missed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


class OutcomeStatus(str, Enum):
    HELPED = "helped"
    NOT_HELPED = "not_helped"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class NotificationCategory(str, Enum):
    CASE_ASSIGNED = "case_assigned"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    OVERDUE_ALERT = "overdue_alert"
    CASE_UPDATED = "case_updated"


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
