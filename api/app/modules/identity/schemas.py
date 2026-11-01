from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "counsellor"
    campus_id: Optional[str] = "campus-1"
    avatar_url: Optional[str] = None


class CampusMembershipOut(BaseModel):
    id: Optional[str] = None
    campus_id: str
    role: str
    department: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    memberships: List[CampusMembershipOut] = []


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    memberships: List[CampusMembershipOut] = []

    class Config:
        from_attributes = True


class IdentityBase(BaseModel):
    pass


class IdentityResponse(IdentityBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
