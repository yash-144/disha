from app.core.permissions import Role

# Staff who already see the underlying case / observation data. Institution admins are excluded on purpose:
# they do not work individual cases. Platform admin passes require_role.
CASE_AI_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.HOD, Role.MENTOR]
EVIDENCE_AI_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.HOD]
STATUS_ROLES = [Role.COUNSELLOR, Role.FACULTY, Role.HOD, Role.MENTOR, Role.INSTITUTION_ADMIN]
ALLOWED_ROLES = sorted({*CASE_AI_ROLES, *EVIDENCE_AI_ROLES}, key=lambda r: r.value)
