"""Notification templates, rendered at send time from IDs and state names only (OUT-04)."""
from typing import Dict, Tuple

# template_key -> (notification_type, title, body format using safe_payload keys)
_TEMPLATES: Dict[str, Tuple[str, str, str]] = {
    "CASE_ASSIGNED": ("case_lifecycle", "New Case Assigned", "Case status changed from {from_state} to {to_state}."),
    "CASE_CLOSED": ("case_lifecycle", "Case Closed", "Case status changed from {from_state} to {to_state}."),
    "CASE_DISMISSED": ("case_lifecycle", "Case Dismissed", "Case status changed from {from_state} to {to_state}."),
    "CASE_REOPENED": ("case_lifecycle", "Case Reopened", "Case status changed from {from_state} to {to_state}."),
    "CASE_ESCALATION_OWNER": (
        "case_escalation", "Case Deadline Passed",
        "A case you own is past its deadline and was escalated (level {level}).",
    ),
    "CASE_ESCALATION_SUPERVISOR": (
        "case_escalation", "Overdue Case Escalated",
        "A case is past its deadline and needs supervisor attention (level {level}).",
    ),
    "FOLLOWUP_OVERDUE_OWNER": ("followup", "Follow-up Overdue", "A scheduled follow-up has passed without being completed."),
    "FOLLOWUP_ESCALATION_SUPERVISOR": (
        "followup_escalation", "Overdue Follow-up Escalated", "A scheduled follow-up is overdue and was escalated.",
    ),
    "SESSION_SCHEDULED": ("session", "Counselling Session Scheduled", "A counselling session was scheduled for {scheduled_at}."),
    "SESSION_CANCELLED": ("session", "Counselling Session Cancelled", "A counselling session planned for {scheduled_at} was cancelled."),
    "SESSION_RESCHEDULED": ("session", "Counselling Session Rescheduled", "A counselling session was moved to {scheduled_at}."),
}


class _Safe(dict):
    def __missing__(self, key):
        return ""


def render(template_key: str, payload: dict) -> Tuple[str, str, str]:
    """Return (notification_type, title, body). Unknown keys raise KeyError (dead-lettered by the dispatcher)."""
    ntype, title, body = _TEMPLATES[template_key]
    return ntype, title, body.format_map(_Safe(payload or {}))


def known(template_key: str) -> bool:
    return template_key in _TEMPLATES
