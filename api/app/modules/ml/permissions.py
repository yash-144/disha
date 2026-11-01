from app.core.permissions import Role

# Platform admins pass every role gate (see require_role).
# INSIGHTS_SPEC.md defines mentor-facing insights only, so students get no read access to scores.
READ_ROLES = (Role.FACULTY, Role.MENTOR, Role.HOD, Role.COUNSELLOR, Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN)
RUN_ROLES = (Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN)
ALLOWED_ROLES = list(READ_ROLES)
