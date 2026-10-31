from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
from app.core.security import decode_access_token
from app.core.permissions import Role

async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_campus_id: Optional[str] = Header(None, alias="X-Campus-ID")
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )
        
    campus_id = x_campus_id or payload.get("campus_id")
    if not campus_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing campus tenancy identifier (X-Campus-ID)"
        )
        
    payload["active_campus_id"] = campus_id
    return payload

def require_roles(*roles: Role):
    def role_verifier(current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = current_user.get("roles", [])
        if not any(r.value in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of {[r.value for r in roles]}"
            )
        return current_user
    return role_verifier
