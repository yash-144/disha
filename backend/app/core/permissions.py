from enum import Enum
from typing import Set

class Role(str, Enum):
    # Canonical role enumeration matching DISHA requirement FR-ROLE-01.
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
    Role.FACULTY, Role.MENTOR, Role.HOD, Role.COUNSELLOR,
    Role.FINANCE, Role.PLACEMENT, Role.LEADERSHIP, Role.INSTITUTION_ADMIN
}
