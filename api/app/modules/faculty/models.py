import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now


class FacultyProfile(Base):
    __tablename__ = "disha_faculty_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, unique=True, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    department = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id], lazy="selectin")


class Course(Base):
    __tablename__ = "disha_courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="Computer Science & IT", nullable=False)
    credits = Column(Integer, default=4, nullable=False)
    semester = Column(String(50), default="Fall 2025", nullable=False)
    primary_faculty_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    primary_faculty = relationship("User", foreign_keys=[primary_faculty_id], lazy="selectin")
    sections = relationship("CourseSection", back_populates="course", cascade="all, delete-orphan", lazy="select")


class CourseSection(Base):
    __tablename__ = "disha_course_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("disha_courses.id"), nullable=False, index=True)
    faculty_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    section_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    term = Column(String(100), default="July - Dec 2025", nullable=False)
    access_code = Column(String(50), unique=True, nullable=False)
    subject = Column(String(100), default="Computer Science", nullable=False)
    color = Column(String(50), default="bg-blue-600", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    course = relationship("Course", back_populates="sections", lazy="selectin")
    faculty = relationship("User", foreign_keys=[faculty_id], lazy="selectin")
    enrollments = relationship("CourseEnrollment", back_populates="section", cascade="all, delete-orphan", lazy="select")
    attendance_records = relationship("StudentAttendanceRecord", back_populates="section", cascade="all, delete-orphan", lazy="select")
    assessments = relationship("Assessment", back_populates="section", cascade="all, delete-orphan", lazy="select")


class CourseEnrollment(Base):
    __tablename__ = "disha_course_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("disha_course_sections.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    status = Column(String(50), default="enrolled", nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("section_id", "student_id", name="uq_disha_enrollment_sec_stu"),
    )

    section = relationship("CourseSection", back_populates="enrollments", lazy="selectin")
    student = relationship("Student", lazy="selectin")


class StudentAttendanceRecord(Base):
    __tablename__ = "disha_attendance_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("disha_course_sections.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    date = Column(String(20), nullable=False)
    status = Column(String(50), nullable=False)
    recorded_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    section = relationship("CourseSection", back_populates="attendance_records", lazy="selectin")
    student = relationship("Student", lazy="selectin")
    recorder = relationship("User", foreign_keys=[recorded_by], lazy="selectin")


class Assessment(Base):
    __tablename__ = "disha_assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    section_id = Column(String(36), ForeignKey("disha_course_sections.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    assessment_type = Column(String(50), default="quiz", nullable=False)
    total_marks = Column(Float, default=100.0, nullable=False)
    clo_code = Column(String(50), default="CLO-1", nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    section = relationship("CourseSection", back_populates="assessments", lazy="selectin")
    creator = relationship("User", foreign_keys=[created_by], lazy="selectin")
    submissions = relationship("AssessmentSubmission", back_populates="assessment", cascade="all, delete-orphan", lazy="select")


class AssessmentSubmission(Base):
    __tablename__ = "disha_assessment_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("disha_assessments.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    graded_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=True, index=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_disha_sub_assessment_stu"),
    )

    assessment = relationship("Assessment", back_populates="submissions", lazy="selectin")
    student = relationship("Student", lazy="selectin")
    grader = relationship("User", foreign_keys=[graded_by], lazy="selectin")
