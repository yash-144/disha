import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now


class SupportRequest(Base):
    __tablename__ = "disha_support_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    faculty_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("disha_courses.id"), nullable=True, index=True)
    category = Column(String(100), nullable=False)
    preferred_slot = Column(String(100), nullable=False)
    student_note = Column(Text, nullable=False)
    status = Column(String(50), default="requested", nullable=False)
    faculty_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    student = relationship("Student", lazy="selectin")
    faculty = relationship("User", foreign_keys=[faculty_id], lazy="selectin")
    course = relationship("Course", foreign_keys=[course_id], lazy="selectin")
