import uuid
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey, Index, UniqueConstraint, text
from app.core.database import Base
from app.modules.audit.models import JSONType
from app.shared.utils import utc_now


class PolicyVersion(Base):
    """Campus policy definition. `draft` is editable; `active`/`retired` are immutable (POL-02)."""
    __tablename__ = "disha_policy_versions"
    __table_args__ = (
        UniqueConstraint("campus_id", "version", name="uq_policy_campus_version"),
        Index("uq_policy_one_active_per_campus", "campus_id", unique=True,
              postgresql_where=text("status = 'active'"), sqlite_where=text("status = 'active'")),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft | active | retired
    definition = Column(JSONType, nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256 of canonical definition (POL-03)
    note = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    published_by = Column(String(36), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)


class PolicyEvaluation(Base):
    """One non-dry-run evaluation of a batch of risk flags."""
    __tablename__ = "disha_policy_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    policy_version_id = Column(String(36), ForeignKey("disha_policy_versions.id"), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False)
    flags_received = Column(Integer, nullable=False, default=0)
    cases_created = Column(Integer, nullable=False, default=0)
    skipped_summary = Column(JSONType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class PolicyDecision(Base):
    """Per-flag outcome of an evaluation; keeps the evidence packet for created cases."""
    __tablename__ = "disha_policy_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String(36), ForeignKey("disha_policy_evaluations.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), nullable=True, index=True)
    external_student_ref_hash = Column(String(128), nullable=True)
    course_ref = Column(String(200), nullable=True)
    tier = Column(String(20), nullable=False)
    probability = Column(Float, nullable=True)
    score_id = Column(String(100), nullable=True)
    decision = Column(String(30), nullable=False)  # case_created | skipped
    reason_code = Column(String(60), nullable=False)
    case_id = Column(String(36), nullable=True, index=True)
    signal_id = Column(String(36), nullable=True)
    evidence = Column(JSONType, nullable=True)
    digest = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


# Backwards compatibility alias for initial scaffold references
PolicyEntity = PolicyVersion
