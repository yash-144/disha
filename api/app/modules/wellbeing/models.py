import uuid
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from app.core.database import Base
from app.modules.audit.models import JSONType
from app.shared.utils import utc_now


class PulseQuestionnaire(Base):
    """Versioned questionnaire (PUL-01)."""
    __tablename__ = "disha_pulse_questionnaires"
    __table_args__ = (UniqueConstraint("campus_id", "version_key", name="uq_pulse_q_version"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    version_key = Column(String(50), nullable=False)
    questions = Column(JSONType, nullable=False)  # [{key, dimension, text}]
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PulsePeriod(Base):
    """Reporting period with start/end; "current" is computed from these (PUL-05)."""
    __tablename__ = "disha_pulse_periods"
    __table_args__ = (UniqueConstraint("campus_id", "label", name="uq_pulse_period_label"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    questionnaire_id = Column(String(36), ForeignKey("disha_pulse_questionnaires.id"), nullable=False)
    label = Column(String(50), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PulseSubmission(Base):
    """One per student per period (PUL-02). `reflection_ciphertext` is restricted data (PUL-04)."""
    __tablename__ = "disha_pulse_submissions"
    __table_args__ = (UniqueConstraint("student_id", "period_id", name="uq_pulse_student_period"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    period_id = Column(String(36), ForeignKey("disha_pulse_periods.id"), nullable=False, index=True)
    questionnaire_id = Column(String(36), ForeignKey("disha_pulse_questionnaires.id"), nullable=False)
    responses = Column(JSONType, nullable=False)  # {question_key: 1..5}
    dimension_scores = Column(JSONType, nullable=False)  # {dimension: 0..100 | null}
    index_score = Column(Float, nullable=True)
    department = Column(String(200), nullable=True)  # snapshot for grouped aggregates
    reflection_ciphertext = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


# Backwards compatibility alias for initial scaffold references
WellbeingEntity = PulseSubmission
