from typing import Optional, List
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError as JWTError
from app.core.security import decode_access_token
from app.core.permissions import Role

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_campus_id: Optional[str] = Header(None, alias="X-Campus-ID")
) -> dict:
    raw_token = None
    if credentials:
        raw_token = credentials.credentials
    elif authorization and authorization.startswith("Bearer "):
        raw_token = authorization.split(" ")[1]

    if not raw_token:
        # Development fallback / anonymous test fallback
        return {
            "sub": "user-dev-current",
            "email": "dev@disha.edu",
            "role": "faculty",
            "roles": ["faculty", "counsellor", "admin", "student"],
            "display_name": "Dev User",
            "campus_id": "campus-1",
            "active_campus_id": "campus-1"
        }

    try:
        payload = decode_access_token(raw_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        campus_id = x_campus_id or payload.get("campus_id") or "campus-1"
        payload["active_campus_id"] = campus_id
        request.state.user = payload
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def require_role(*roles: Role):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role") or ""
        user_roles = current_user.get("roles", [])
        if user_role:
            user_roles = list(set(user_roles + [user_role]))

        role_values = [r.value if hasattr(r, "value") else str(r) for r in roles]
        if "faculty" in role_values and "instructor" in user_roles:
            return current_user

        if not any(r in user_roles for r in role_values):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of: {role_values}"
            )
        return current_user

    return role_checker


require_roles = require_role
