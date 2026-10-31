from typing import Optional
from fastapi import Depends, HTTPException, Request, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import Role

security_scheme = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.DISHA_JWT_SECRET,
            algorithms=[settings.DISHA_JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

def require_role(*roles: Role):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(r.value in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation"
            )
        return current_user
    return role_checker


async def get_campus_member(request: Request, user: dict = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)) -> str:
    """X-Campus-ID is only honoured when the token's user has an active membership there (else 403)."""
    campus_id = request.headers.get("X-Campus-ID")
    if not campus_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "X-Campus-ID header is required")
    from app.modules.campus.models import CampusMembership
    q = select(CampusMembership.id).where(
        CampusMembership.user_id == str(user.get("sub", "")), CampusMembership.campus_id == campus_id,
        CampusMembership.is_active.is_(True)).limit(1)
    if (await db.execute(q)).first() is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this campus")
    request.state.campus_id = campus_id
    return campus_id


def campus_role(*roles: Role):
    """Role guard plus campus membership guard; returns the token payload."""
    role_checker = require_role(*roles)

    async def checker(user: dict = Depends(role_checker), _campus: str = Depends(get_campus_member)):
        return user
    return checker
