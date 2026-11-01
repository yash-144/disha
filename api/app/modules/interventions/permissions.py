from app.core.permissions import Role

# Roles that may change interventions / follow-ups; services additionally require case ownership
# unless the caller is an HOD or platform admin (cases/access.py).
CASE_WORK_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.MENTOR, Role.HOD, Role.PLATFORM_ADMIN]
# Institution admins may read (supervisory), not write.
CASE_VIEW_ROLES = CASE_WORK_ROLES + [Role.INSTITUTION_ADMIN]
CATALOGUE_ADMIN_ROLES = [Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN]
ALLOWED_ROLES = CASE_VIEW_ROLES
