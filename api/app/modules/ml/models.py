"""Scoring runs and per-enrolment risk scores of the rolling model (INSIGHTS_SPEC.md)."""
import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.shared.utils import utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")

RUN_RUNNING = "running"
RUN_COMPLETED = "completed"
RUN_FAILED = "failed"


def _id() -> str:
    return str(uuid.uuid4())


class MlScoringRun(Base):
    __tablename__ = "disha_ml_runs"

    id = Column(String(36), primary_key=True, default=_id)
    campus_id = Column(String(36), nullable=False, index=True)
    triggered_by = Column(String(100), nullable=False)          # user id, or "scheduler"
    status = Column(String(20), nullable=False, index=True)
    term_id = Column(String(100), nullable=True)                # null = all terms in the data
    as_of_day = Column(Integer, nullable=False)                 # days since term start
    model_version = Column(String(100), nullable=False)         # e.g. "rolling-hgb-isotonic/v1"
    bundle_sha256 = Column(String(64), nullable=True)
    schema_version = Column(String(20), nullable=True)
    batch_ids = Column(JSONType, nullable=False, default=list)  # import batches the run read
    n_scored = Column(Integer, nullable=False, default=0)
    tier_counts = Column(JSONType, nullable=False, default=dict)
    cohorts = Column(JSONType, nullable=True)                   # CohortInsight list (aggregate)
    data_drift = Column(JSONType, nullable=True)                # DriftReport (PSI vs training reference)
    model_info = Column(JSONType, nullable=True)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)


class MlRiskScore(Base):
    __tablename__ = "disha_ml_scores"
    __table_args__ = (
        Index("ix_disha_ml_scores_run_tier", "run_id", "tier"),
        Index("ix_disha_ml_scores_campus_hash", "campus_id", "external_student_ref_hash"),
    )

    id = Column(String(36), primary_key=True, default=_id)
    run_id = Column(String(36), ForeignKey("disha_ml_runs.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)           # id exactly as the campus supplied it
    external_student_ref_hash = Column(String(40), nullable=False)
    student_id = Column(String(36), nullable=True, index=True)  # roster student id when linked
    course_id = Column(String(100), nullable=False)
    term_id = Column(String(100), nullable=False)
    as_of_day = Column(Integer, nullable=False)
    as_of_date = Column(String(10), nullable=True)              # ISO date when term_start is known
    probability = Column(Float, nullable=False)
    tier = Column(String(10), nullable=False)                   # HIGH | MEDIUM | WATCH | ON_TRACK
    signal = Column(Boolean, nullable=False, default=False)
    previous_probability = Column(Float, nullable=True)
    previous_tier = Column(String(10), nullable=True)
    direction = Column(String(10), nullable=True)               # up | down | steady | new
    reasons = Column(JSONType, nullable=False, default=list)
    insight = Column(JSONType, nullable=False, default=dict)    # the full StudentInsight dict (spec section 5)
    model_version = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
