from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

Tier = Literal["high", "medium", "watch", "none"]
Priority = Literal["low", "medium", "high", "urgent"]
PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2, "urgent": 3}
TIER_RANK = {"none": 0, "watch": 1, "medium": 2, "high": 3}


class RiskFlagIn(Protocol):
    """Shape of a risk flag from the ML pipeline (mirrors app.modules.ml.schemas.RiskFlag)."""
    campus_id: str
    student_id: Optional[str]
    external_student_ref_hash: Optional[str]
    course_ref: Optional[str]
    as_of: Any
    tier: str
    probability: float
    reasons: List[Dict[str, Any]]
    model_version: str
    score_id: Optional[str]


class RiskFlagPayload(BaseModel):
    """Concrete RiskFlagIn for the dry-run endpoint."""
    campus_id: Optional[str] = None  # defaults to the caller's campus
    student_id: Optional[str] = None
    external_student_ref_hash: Optional[str] = None
    course_ref: Optional[str] = None
    as_of: Optional[datetime] = None
    tier: Tier
    probability: float = Field(..., ge=0, le=1)
    reasons: List[Dict[str, Any]] = Field(default_factory=list)
    model_version: str = "unknown"
    score_id: Optional[str] = None


# ---- policy definition -------------------------------------------------------------------

class TierRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    min_probability: float = Field(0.0, ge=0, le=1)
    priority: Priority = "medium"
    due_in_days: Optional[int] = Field(None, ge=1, le=365)


class ReasonRule(BaseModel):
    """Rule-based signal on the model's reasons (blueprint 06 §3: rationale code per rule)."""
    model_config = ConfigDict(extra="forbid")
    rule_key: str = Field(..., min_length=1, max_length=100)
    reason_groups: List[str] = Field(..., min_length=1)
    min_effect_pts: float = 0.0
    min_tier: Literal["high", "medium", "watch"] = "watch"
    action: Literal["open_case", "raise_priority"] = "raise_priority"
    priority: Priority = "high"


class CapacityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_new_cases_per_evaluation: Optional[int] = Field(None, ge=0)
    max_open_cases: Optional[int] = Field(None, ge=0)


class PolicyDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tiers: Dict[str, TierRule]
    cooldown_days: int = Field(14, ge=0, le=730)
    initial_state: Literal["suggested", "under_review", "action_planned"] = "suggested"
    capacity: CapacityConfig = Field(default_factory=CapacityConfig)
    reason_rules: List[ReasonRule] = Field(default_factory=list)

    @field_validator("tiers")
    @classmethod
    def _tier_keys(cls, v: Dict[str, TierRule]) -> Dict[str, TierRule]:
        bad = set(v) - {"high", "medium", "watch"}
        if bad:
            raise ValueError(f"unknown tier keys: {sorted(bad)}")
        if not v:
            raise ValueError("at least one tier must be configured")
        return v


class PolicyVersionCreate(BaseModel):
    definition: PolicyDefinition
    note: Optional[str] = Field(None, max_length=2000)


class PolicyVersionUpdate(BaseModel):
    definition: Optional[PolicyDefinition] = None
    note: Optional[str] = Field(None, max_length=2000)


class PolicyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campus_id: str
    version: int
    status: str
    definition: Dict[str, Any]
    checksum: str
    note: Optional[str] = None
    created_by: str
    created_at: datetime
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None


# ---- evaluation --------------------------------------------------------------------------

class DryRunRequest(BaseModel):
    flags: List[RiskFlagPayload] = Field(..., max_length=5000)
    policy_version_id: Optional[str] = Field(None, description="Draft or published version to try; default is the active one")


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[str] = None
    student_id: Optional[str] = None
    external_student_ref_hash: Optional[str] = None
    course_ref: Optional[str] = None
    tier: str
    probability: Optional[float] = None
    decision: str
    reason_code: str
    case_id: Optional[str] = None
    digest: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None


class PolicyEvaluationResult(BaseModel):
    evaluation_id: Optional[str] = None
    policy_version_id: str
    policy_version: int
    dry_run: bool
    flags_received: int
    cases_created: int  # in a dry run: number of cases that would be created
    skipped: Dict[str, int]
    decisions: List[DecisionResponse]


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    campus_id: str
    policy_version_id: str
    actor_id: str
    flags_received: int
    cases_created: int
    skipped_summary: Dict[str, int]
    created_at: datetime


# Backwards compatibility alias for the scaffold
PolicyResponse = PolicyVersionResponse
