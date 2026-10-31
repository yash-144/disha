from app.core.permissions import Role

# Uploading data and reading import history is an admin act (platform admins pass every role gate).
ALLOWED_ROLES = [Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN]
IMPORT_ROLES = (Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN)
