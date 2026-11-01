import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now
from app.modules.identity.models import User
from app.modules.roster.models import Student


class CounsellorProfile(Base):
    __tablename__ = "disha_counsellor_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, unique=True, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    department = Column(String(200), nullable=True)
    specialisation = Column(String(300), nullable=True)
    designation = Column(String(200), nullable=True)
    phone = Column(String(40), nullable=True)
    availability_status = Column(String(30), nullable=False, default="available")  # available | in_session | away
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")


class CounsellorAssignment(Base):
    __tablename__ = "disha_counsellor_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    counsellor_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    counsellor = relationship("User", foreign_keys=[counsellor_id], lazy="selectin")
    student = relationship("Student", foreign_keys=[student_id], lazy="selectin")


class CounsellingSession(Base):
    """A scheduled counselling appointment. Contains no clinical content (see CounsellingNote)."""
    __tablename__ = "disha_counselling_sessions"
    __table_args__ = (Index("ix_disha_counselling_sessions_counsellor_time", "counsellor_id", "scheduled_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=True, index=True)
    counsellor_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=45)
    mode = Column(String(30), nullable=False, default="in_person")  # in_person | video | phone
    location = Column(String(300), nullable=True)
    status = Column(String(30), nullable=False, default="scheduled", index=True)  # scheduled|completed|cancelled|no_show
    cancel_reason = Column(String(500), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    student = relationship("Student", foreign_keys=[student_id], lazy="selectin")


class CounsellingNote(Base):
    """Confidential counselling note. Readable only by counsellors in scope for the student."""
    __tablename__ = "disha_counselling_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=True, index=True)
    session_id = Column(String(36), ForeignKey("disha_counselling_sessions.id"), nullable=True)
    author_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
CounsellingEntity = CounsellorProfile
