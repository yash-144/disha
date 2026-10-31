from app.core.permissions import Role

# Who may create / read documents. Platform admin is always allowed by require_role.
UPLOAD_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.HOD, Role.INSTITUTION_ADMIN]
READ_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.HOD, Role.INSTITUTION_ADMIN]
# Anchoring publishes a hash outside the institution, so it is an administrative act.
ANCHOR_ROLES = [Role.INSTITUTION_ADMIN]
# Roles that see every document of the campus; the others see their own uploads and documents of cases assigned to them.
CAMPUS_WIDE_ROLES = {Role.INSTITUTION_ADMIN, Role.HOD, Role.PLATFORM_ADMIN}
ALLOWED_ROLES = sorted({*UPLOAD_ROLES, *READ_ROLES}, key=lambda r: r.value)
