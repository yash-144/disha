import uuid
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now


class Student(Base):
    __tablename__ = "disha_roster"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_uid = Column(String(100), nullable=False, index=True)
    full_name = Column(String(300), nullable=False)
    email = Column(String(320), nullable=True)
    department = Column(String(200), nullable=True)
    course = Column(String(200), nullable=True)
    academic_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    observations = relationship("Observation", back_populates="student", cascade="all, delete-orphan", lazy="selectin")


class Observation(Base):
    __tablename__ = "disha_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    domain = Column(String(50), nullable=False)
    source = Column(String(100), nullable=True)
    data = Column(Text, nullable=True)
    observed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="observations", lazy="selectin")


# Backwards compatibility alias for initial scaffold references
RosterEntity = Student
