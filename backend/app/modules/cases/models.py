import uuid
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, ForeignKey, Float, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from app.core.database import Base
from app.shared.utils import utc_now
from app.shared.enums import CaseStatus, CaseState, map_status_to_state, map_state_to_status
from app.modules.identity.models import User
from app.modules.roster.models import Student

# Universal JSON type supporting PostgreSQL JSONB in production and SQLite JSON in tests
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Signal(Base):
    __tablename__ = "disha_signals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    rule_key = Column(String(100), nullable=False)
    result = Column(String(50), default="attention_suggested", nullable=False)
    ml_risk_probability = Column(Float, nullable=True)
    ml_tier = Column(String(50), nullable=True)
    evidence_snapshot = Column(Text, nullable=True)
    reviewed = Column(Boolean, default=False, nullable=False)
    reviewed_decision = Column(String(50), nullable=True)
    review_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    student = relationship("Student", foreign_keys=[student_id], lazy="selectin")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="selectin")


class Case(Base):
    __tablename__ = "disha_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    assigned_counsellor_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=True, index=True)
    originating_signal_id = Column(String(36), ForeignKey("disha_signals.id"), unique=True, nullable=True)
    status = Column(String(30), nullable=False, default=CaseStatus.NEW.value, index=True)
    priority = Column(String(20), nullable=False, default="medium")
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    student = relationship("Student", foreign_keys=[student_id], lazy="selectin")
    assigned_counsellor = relationship("User", foreign_keys=[assigned_counsellor_id], lazy="selectin")
    signal = relationship("Signal", foreign_keys=[originating_signal_id], lazy="selectin")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan", lazy="selectin")
    events = relationship("CaseEvent", back_populates="case", cascade="all, delete-orphan", lazy="selectin")
    interventions = relationship("Intervention", back_populates="case", cascade="all, delete-orphan", lazy="selectin")
    followups = relationship("FollowUp", back_populates="case", cascade="all, delete-orphan", lazy="selectin")

    @validates("status")
    def validate_status(self, key, value):
        if value is None:
            return value
        if isinstance(value, CaseState):
            return value.value
        if isinstance(value, CaseStatus):
            return value.value
        if isinstance(value, str):
            val_lower = value.strip().lower()
            if val_lower in {s.value for s in CaseState} or val_lower in {s.value for s in CaseStatus}:
                return val_lower
            raise ValueError(
                f"Invalid case status: '{value}'. Must be a valid canonical CaseState or legacy CaseStatus."
            )
        raise ValueError(f"Invalid case status type: {type(value)}")

    # Canonical 14-state machine integration
    @property
    def state(self) -> str:
        """Returns the canonical 14-state machine value as a string."""
        return map_status_to_state(self.status).value

    @state.setter
    def state(self, value) -> None:
        if isinstance(value, CaseState):
            self.status = value.value
        elif isinstance(value, str):
            val_lower = value.strip().lower()
            if val_lower in {s.value for s in CaseState}:
                self.status = val_lower
            elif val_lower in {s.value for s in CaseStatus}:
                self.status = map_status_to_state(val_lower).value
            else:
                raise ValueError(
                    f"Invalid case state: '{value}'. Must be one of {[s.value for s in CaseState]}"
                )
        elif value is not None:
            raise ValueError(f"Invalid case state type: {type(value)}")

    @property
    def legacy_status(self) -> str:
        """Returns the legacy 6-state status for backward compatibility."""
        return map_state_to_status(self.status).value


class CaseNote(Base):
    __tablename__ = "disha_case_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    author_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    case = relationship("Case", back_populates="notes", lazy="selectin")


class CaseEvent(Base):
    __tablename__ = "disha_case_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    case = relationship("Case", back_populates="events", lazy="selectin")


class InterventionCatalogue(Base):
    __tablename__ = "disha_intervention_catalogue"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    interventions = relationship("Intervention", back_populates="catalogue_entry", lazy="selectin")


class Intervention(Base):
    __tablename__ = "disha_interventions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    catalogue_id = Column(String(36), ForeignKey("disha_intervention_catalogue.id"), nullable=False, index=True)
    counsellor_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    progress = Column(String(50), nullable=False, default="not_started")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    case = relationship("Case", back_populates="interventions", lazy="selectin")
    catalogue_entry = relationship("InterventionCatalogue", back_populates="interventions", lazy="selectin")
    outcome = relationship("InterventionOutcome", back_populates="intervention", uselist=False, lazy="selectin")


class InterventionOutcome(Base):
    __tablename__ = "disha_intervention_outcomes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    intervention_id = Column(String(36), ForeignKey("disha_interventions.id"), nullable=False, unique=True, index=True)
    counsellor_id = Column(String(36), nullable=False)
    campus_id = Column(String(36), nullable=False)
    completion_status = Column(String(50), nullable=False)
    outcome_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    intervention = relationship("Intervention", back_populates="outcome", lazy="selectin")


class FollowUp(Base):
    __tablename__ = "disha_followups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    counsellor_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), nullable=False, default="scheduled")
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    case = relationship("Case", back_populates="followups", lazy="selectin")
    followup_notes = relationship("FollowUpNote", back_populates="followup", cascade="all, delete-orphan", lazy="selectin")


class FollowUpNote(Base):
    __tablename__ = "disha_followup_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    followup_id = Column(String(36), ForeignKey("disha_followups.id"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=False, index=True)
    author_id = Column(String(36), nullable=False)
    campus_id = Column(String(36), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    followup = relationship("FollowUp", back_populates="followup_notes", lazy="selectin")


# Backwards compatibility alias for initial scaffold references
CasesEntity = Case
