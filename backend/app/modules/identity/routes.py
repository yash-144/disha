from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.entities import UserProfile, InstitutionMembership, StudentAccountLink

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    role: str
    title: Optional[str] = None
    avatar: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(UserProfile).where(UserProfile.email == payload.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    # Fetch user roles
    mem_stmt = select(InstitutionMembership.role).where(
        InstitutionMembership.user_id == user.id,
        InstitutionMembership.is_active == True
    )
    roles = (await db.execute(mem_stmt)).scalars().all()
    primary_role = user.role or (roles[0] if roles else "student")

    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.display_name,
        "role": primary_role,
        "roles": list(set([primary_role] + list(roles)))
    }
    token = create_access_token(token_data)

    return LoginResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.display_name,
        role=primary_role,
        title=user.title,
        avatar=user.avatar
    )


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get("sub")
    user = (await db.execute(select(UserProfile).where(UserProfile.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.display_name,
        "role": user.role,
        "title": user.title,
        "avatar": user.avatar,
        "bio": user.bio
    }
