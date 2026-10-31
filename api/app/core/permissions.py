from enum import Enum
from typing import Set, Dict


class Role(str, Enum):
    """Canonical role enumeration matching DISHA requirement FR-ROLE-01."""
    STUDENT = "student"
    FACULTY = "faculty"
    MENTOR = "mentor"
    HOD = "hod"
    COUNSELLOR = "counsellor"
    FINANCE = "finance"
    PLACEMENT = "placement"
    LEADERSHIP = "leadership"
    INSTITUTION_ADMIN = "institution_admin"
    PLATFORM_ADMIN = "platform_admin"


STAFF_ROLES: Set[Role] = {
    Role.FACULTY,
    Role.MENTOR,
    Role.HOD,
    Role.COUNSELLOR,
    Role.FINANCE,
    Role.PLACEMENT,
    Role.LEADERSHIP,
    Role.INSTITUTION_ADMIN,
}


class Action(str, Enum):
    # Platform Configuration
    MANAGE_PLATFORM_CONFIG = "platform.config.manage"

    # Campus User & Identity Management
    MANAGE_CAMPUS_USERS = "campus.users.manage"
    VIEW_INSTITUTIONAL_DASHBOARD = "dashboard.institutional.view"

    # Cases
    VIEW_ASSIGNED_CASES = "case.assigned.view"
    UPDATE_ASSIGNED_CASES = "case.assigned.update"
    ASSIGN_CASES = "case.assign"

    # Interventions & Follow-ups
    MANAGE_INTERVENTIONS = "intervention.manage"
    MANAGE_FOLLOWUPS = "followup.manage"

    # Clinical & Confidential Counselling Notes
    VIEW_CONFIDENTIAL_NOTES = "counselling.notes.confidential.view"
    CREATE_CONFIDENTIAL_NOTES = "counselling.notes.confidential.create"

    # Audit Trail
    VIEW_AUDIT_HISTORY = "audit.history.view"


# Role-to-Action Permission Matrix per DISHA Security Blueprint & Specification
ACTION_PERMISSIONS: Dict[Action, Set[Role]] = {
    Action.MANAGE_PLATFORM_CONFIG: {Role.PLATFORM_ADMIN},
    Action.MANAGE_CAMPUS_USERS: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN},
    Action.VIEW_INSTITUTIONAL_DASHBOARD: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN},
    Action.VIEW_ASSIGNED_CASES: {
        Role.PLATFORM_ADMIN,
        Role.INSTITUTION_ADMIN,
        Role.COUNSELLOR,
        Role.FACULTY,
        Role.HOD,
        Role.MENTOR,
    },
    Action.UPDATE_ASSIGNED_CASES: {Role.PLATFORM_ADMIN, Role.COUNSELLOR},
    Action.ASSIGN_CASES: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN, Role.HOD},
    Action.MANAGE_INTERVENTIONS: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN, Role.COUNSELLOR},
    Action.MANAGE_FOLLOWUPS: {Role.PLATFORM_ADMIN, Role.COUNSELLOR},
    # CRITICAL: Institution Admin has NO permission to view or create confidential counselling notes!
    Action.VIEW_CONFIDENTIAL_NOTES: {Role.COUNSELLOR},
    Action.CREATE_CONFIDENTIAL_NOTES: {Role.COUNSELLOR},
    Action.VIEW_AUDIT_HISTORY: {
        Role.PLATFORM_ADMIN,
        Role.INSTITUTION_ADMIN,
        Role.COUNSELLOR,
        Role.FACULTY,
    },
}
