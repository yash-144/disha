from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    roles: List[str]
    campus_id: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: List[str]
    campus_id: str
    created_at: datetime
