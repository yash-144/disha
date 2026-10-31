from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- policy handoff contract (consumed by the policy module) --------------------------------
@dataclass
class RiskFlag:
    """One scored enrolment. `tier` is lower case: 'high' | 'medium' | 'watch' | 'none' (ON_TRACK).

    `course_ref` is "<course_id>:<term_id>". `student_id` is the roster id, or None when the campus id
    could not be linked to a roster student. `external_student_ref_hash` is the pseudonym that is safe
    to log or send to Meko.
    """
    campus_id: str
    student_id: Optional[str]
    external_student_ref_hash: str
    course_ref: str
    as_of: str                      # ISO date when known, else "day:<n>"
    tier: str
    probability: float
    reasons: List[Dict[str, Any]]
    model_version: str
    score_id: str


# ---- API schemas ------------------------------------------------------------------------------
class ScoringRunRequest(BaseModel):
    as_of_day: Optional[int] = Field(None, ge=0, le=3650, description="days since term start")
    as_of_date: Optional[date] = Field(None, description="calendar date; needs term_id and enrolments.term_start")
    term_id: Optional[str] = Field(None, description="score only this term (recommended)")


class ScoringRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campus_id: str
    triggered_by: str
    status: str
    term_id: Optional[str] = None
    as_of_day: int
    model_version: str
    bundle_sha256: Optional[str] = None
    schema_version: Optional[str] = None
    batch_ids: List[str]
    n_scored: int
    tier_counts: Dict[str, int]
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class RunPage(BaseModel):
    items: List[ScoringRunResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RiskScoreSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    student_ref: str
    external_student_ref_hash: str
    student_id: Optional[str] = None
    course_id: str
    term_id: str
    as_of_day: int
    as_of_date: Optional[str] = None
    probability: float
    tier: str
    signal: bool
    previous_tier: Optional[str] = None
    previous_probability: Optional[float] = None
    direction: Optional[str] = None
    reasons: List[Dict[str, Any]]
    model_version: str


class RiskScorePage(BaseModel):
    run_id: str
    as_of_day: int
    items: List[RiskScoreSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentInsightResponse(BaseModel):
    """Latest insight per enrolment for one student; `insight` is StudentInsight (INSIGHTS_SPEC section 5)."""
    student_id: Optional[str]
    external_student_ref_hash: str
    student_ref: str
    items: List["EnrolmentInsight"]


class EnrolmentInsight(BaseModel):
    score: RiskScoreSummary
    insight: Dict[str, Any]


StudentInsightResponse.model_rebuild()


class CohortInsightsResponse(BaseModel):
    run_id: str
    as_of_day: int
    cohorts: List[Dict[str, Any]]      # CohortInsight (INSIGHTS_SPEC section 6)


class DriftResponse(BaseModel):
    run_id: str
    as_of_day: int
    finished_at: Optional[datetime]
    data_drift: Dict[str, Any]         # DriftReport (INSIGHTS_SPEC section 7)


class ModelInfoResponse(BaseModel):
    model: str
    bundle_version: Optional[int] = None
    model_version: str
    bundle_sha256: str
    trained_terms: List[str]
    features: List[str]
    cutoffs: Dict[str, Optional[float]]
    capacity_share: Optional[float] = None
    dataset: Optional[str] = None
    headline_metrics: Dict[str, Any] = {}
    notes: List[str]
