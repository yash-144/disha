from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.identity.services import IdentityService
from app.modules.identity.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter()


@router.get("/")
async def list_identity():
    return {"module": "identity", "status": "active"}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user with institutional email and password to receive JWT."""
    result = await IdentityService.login(db, payload.email, payload.password)
    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user_id=result["user_id"],
        email=result["email"],
        full_name=result["full_name"],
        memberships=result["memberships"],
    )


@router.get("/me", response_model=UserOut)
async def get_current_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve authenticated user's current identity profile and campus memberships."""
    user_id = current_user.get("sub")
    user = await IdentityService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    memberships = await IdentityService.get_active_memberships(db, user_id)
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        memberships=[
            {
                "id": m.id,
                "campus_id": m.campus_id,
                "role": m.role,
                "department": m.department,
                "is_active": m.is_active,
            }
            for m in memberships
        ],
    )
