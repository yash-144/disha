from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError as JWTError
from app.core.security import decode_access_token
from app.core.permissions import Role

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    try:
        payload = decode_access_token(credentials.credentials)
        request.state.user = payload
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def require_role(*roles: Role):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role") or ""
        # Also handle plural roles or string match
        user_roles = current_user.get("roles", [])
        if user_role:
            user_roles = list(set(user_roles + [user_role]))

        role_values = [r.value for r in roles]
        # Also map 'instructor' to 'faculty'
        if "faculty" in role_values and "instructor" in user_roles:
            return current_user

        if not any(r in user_roles for r in role_values):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {', '.join(role_values)}"
            )
        return current_user

    return role_checker
