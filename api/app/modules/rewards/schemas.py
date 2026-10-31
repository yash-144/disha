from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AwardRequest(BaseModel):
    student_id: str
    activity_key: str
    source_ref: str = Field(..., min_length=1, max_length=200, description="Event/activity reference; (student, activity, source_ref) is claimed once")
    note: Optional[str] = Field(None, max_length=1000)


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    entry_type: str
    activity_key: Optional[str] = None
    source_ref: Optional[str] = None
    points: int
    reference_id: Optional[str] = None
    created_at: datetime


class BalanceResponse(BaseModel):
    student_id: str
    balance: int


class RewardItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    cost_points: int = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    is_available: bool = True


class RewardItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    cost_points: Optional[int] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_available: Optional[bool] = None


class RewardItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    cost_points: int
    stock: int
    is_available: bool


class RedemptionCreate(BaseModel):
    item_id: str


class RedemptionStatusUpdate(BaseModel):
    status: str = Field(..., description="approved | fulfilled | rejected")
    note: Optional[str] = Field(None, max_length=1000)


class RedemptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    student_id: str
    item_id: str
    cost_points: int
    status: str
    note: Optional[str] = None
    handled_at: Optional[datetime] = None
    created_at: datetime


class ActivityResponse(BaseModel):
    key: str
    points: int
    frequency: str


RewardsResponse = LedgerEntryResponse
