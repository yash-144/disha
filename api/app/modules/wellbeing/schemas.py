from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Question(BaseModel):
    key: str = Field(..., min_length=1, max_length=60)
    dimension: str = Field(..., min_length=1, max_length=60)
    text: str = Field(..., min_length=1, max_length=500)


class QuestionnaireCreate(BaseModel):
    version_key: str = Field(..., min_length=1, max_length=50)
    questions: List[Question] = Field(..., min_length=1)

    @field_validator("questions")
    @classmethod
    def _unique_keys(cls, v):
        keys = [q.key for q in v]
        if len(keys) != len(set(keys)):
            raise ValueError("question keys must be unique")
        return v


class QuestionnaireResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    version_key: str
    questions: List[Dict[str, Any]]
    created_at: datetime


class PeriodCreate(BaseModel):
    questionnaire_id: str
    label: str = Field(..., min_length=1, max_length=50)
    starts_at: datetime
    ends_at: datetime


class PeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    questionnaire_id: str
    label: str
    starts_at: datetime
    ends_at: datetime


class CurrentPulseResponse(BaseModel):
    period: PeriodResponse
    questionnaire: QuestionnaireResponse
    already_submitted: bool


class PulseSubmissionCreate(BaseModel):
    responses: Dict[str, int] = Field(..., description="question key -> 1..5; invalid values are excluded, never scored as 0")
    reflection: Optional[str] = Field(None, max_length=2000)


class PulseSubmissionResponse(BaseModel):
    id: str
    period_id: str
    index_score: Optional[float]
    band: Optional[str]
    dimension_scores: Dict[str, Optional[float]]
    points_awarded: int
    submitted_at: datetime


class PulseStatusResponse(BaseModel):
    period_id: Optional[str]
    completed: bool


class AggregateResponse(BaseModel):
    period_id: str
    suppressed: bool
    response_count: Optional[int]
    eligible_count: int
    participation_rate: Optional[float]
    index_score: Optional[float] = None
    band: Optional[str] = None
    dimension_scores: Optional[Dict[str, Optional[float]]] = None
    by_department: List[Dict[str, Any]] = []
    min_respondents: int


class TrendPoint(BaseModel):
    period_id: str
    label: str
    starts_at: datetime
    suppressed: bool
    response_count: Optional[int] = None
    index_score: Optional[float] = None
    change: Optional[float] = None


WellbeingResponse = PulseSubmissionResponse
