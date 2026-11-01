import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
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


# Backwards compatibility alias for initial scaffold references
CounsellingEntity = CounsellorProfile
