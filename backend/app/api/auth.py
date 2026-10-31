from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    """Authenticate with institutional email and password to receive JWT."""
    user = None
    with db._lock:
        for u in db.users.values():
            if u.get("email").lower() == payload.email.lower().strip():
                user = u
                break

    if not user or not verify_password(payload.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials: incorrect email or password"
        )

    campus_id = user.get("campus_id")
    token_data = {
        "sub": user.get("id"),
        "email": user.get("email"),
        "roles": user.get("roles", []),
        "campus_id": campus_id,
        "full_name": user.get("full_name")
    }
    access_token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=access_token,
        user_id=user.get("id"),
        email=user.get("email"),
        full_name=user.get("full_name"),
        roles=user.get("roles", []),
        campus_id=campus_id
    )

@router.get("/me", response_model=UserProfileResponse)
async def get_my_identity(current_user: dict = Depends(get_current_user)):
    """Retrieve authenticated user identity and role assignment."""
    user_id = current_user.get("sub")
    user = db.users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User record not found")
    return UserProfileResponse(
        id=user.get("id"),
        email=user.get("email"),
        full_name=user.get("full_name"),
        roles=user.get("roles", []),
        campus_id=user.get("campus_id"),
        created_at=user.get("created_at")
    )

