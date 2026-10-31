from app.core.permissions import Role

# Only the student themself may issue / link / mint their identity (NFT-02). Platform admin passes require_role.
STUDENT_ROLES = [Role.STUDENT]
ALLOWED_ROLES = STUDENT_ROLES
