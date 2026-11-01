import uuid
from datetime import datetime, timezone
from typing import Optional
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


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'student', 'faculty', etc.
    title = Column(String(255), nullable=True)
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class InstitutionMembership(Base):
    __tablename__ = "institution_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "user_id", "role", name="uq_inst_user_role"),
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    external_ref = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    cohort_code = Column(String(100), nullable=False)
    enrollment_status = Column(String(50), default="active", nullable=False)
    attendance_rate = Column(Float, default=95.0, nullable=False)
    quiz_score_avg = Column(Float, default=88.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "external_ref", name="uq_inst_student_ref"),
    )


class StudentAccountLink(Base):
    __tablename__ = "student_account_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), unique=True, nullable=False)
    user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    verified_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "user_id", name="uq_inst_user_link"),
    )


class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="Computer Science & IT", nullable=False)
    credits = Column(Integer, default=4, nullable=False)
    semester = Column(String(50), default="Fall 2025", nullable=False)
    primary_faculty_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CourseSection(Base):
    __tablename__ = "course_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=False)
    faculty_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    section_code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    term = Column(String(100), default="July - Dec 2025", nullable=False)
    access_code = Column(String(50), unique=True, nullable=False)
    subject = Column(String(100), default="Computer Science", nullable=False)
    color = Column(String(50), default="bg-blue-600", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    section_id = Column(String(36), ForeignKey("course_sections.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    status = Column(String(50), default="enrolled", nullable=False)
    enrolled_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("section_id", "student_id", name="uq_section_student"),
    )


class StudentAttendanceRecord(Base):
    __tablename__ = "student_attendance_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    section_id = Column(String(36), ForeignKey("course_sections.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    date = Column(String(20), nullable=False)  # 'YYYY-MM-DD'
    status = Column(String(50), nullable=False)  # 'Present', 'Late', 'Absent'
    recorded_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    section_id = Column(String(36), ForeignKey("course_sections.id"), nullable=False)
    title = Column(String(255), nullable=False)
    assessment_type = Column(String(50), default="quiz", nullable=False)  # 'quiz', 'assignment', 'lab'
    total_marks = Column(Float, default=100.0, nullable=False)
    clo_code = Column(String(50), default="CLO-1", nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    assessment_id = Column(String(36), ForeignKey("assessments.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=True)
    graded_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("assessment_id", "student_id", name="uq_assessment_student"),
    )


class SupportRequest(Base):
    __tablename__ = "support_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    faculty_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    course_id = Column(String(36), ForeignKey("courses.id"), nullable=True)
    category = Column(String(100), nullable=False)  # 'concept_doubt', 'assignment_guidance', etc.
    preferred_slot = Column(String(100), nullable=False)
    student_note = Column(Text, nullable=False)
    status = Column(String(50), default="requested", nullable=False)  # 'requested', 'scheduled', 'resolved'
    faculty_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    rule_key = Column(String(100), nullable=False)
    result = Column(String(50), default="attention_suggested", nullable=False)
    ml_risk_probability = Column(Float, nullable=True)
    ml_tier = Column(String(50), nullable=True)  # 'HIGH', 'MEDIUM', 'WATCH'
    evidence_snapshot = Column(Text, nullable=True)  # JSON representation
    reviewed = Column(Boolean, default=False, nullable=False)
    reviewed_decision = Column(String(50), nullable=True)  # 'approve', 'modify', 'dismiss'
    review_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    originating_signal_id = Column(String(36), ForeignKey("signals.id"), unique=True, nullable=True)
    selected_intervention_key = Column(String(100), default="mentor_check_in", nullable=False)
    state = Column(String(50), default="action_planned", nullable=False)
    primary_owner_user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    deadline_version = Column(Integer, default=1, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    follow_up_type = Column(String(100), default="contact_attempt", nullable=False)
    contact_status = Column(String(50), default="student_reached", nullable=True)
    proof_kind = Column(String(100), default="staff_attestation", nullable=False)
    sanitized_note = Column(Text, nullable=False)
    recorded_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    occurred_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), default="info", nullable=False)  # 'alert', 'success', 'info'
    read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProcessingAuthorization(Base):
    __tablename__ = "processing_authorizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    purpose_key = Column(String(100), nullable=False)  # 'early_warning', 'counselling_referral'
    basis_type = Column(String(100), default="legitimate_interest", nullable=False)
    status = Column(String(50), default="active", nullable=False)  # 'active', 'withdrawn', 'expired'
    effective_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StudentObservation(Base):
    __tablename__ = "student_observations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    domain = Column(String(50), nullable=False)  # 'attendance', 'academic', 'participation', 'faculty_feedback'
    metric_key = Column(String(100), nullable=False)  # 'attendance_rate', 'missing_assignments_count', etc.
    value = Column(Float, nullable=False)
    unit = Column(String(50), default="ratio", nullable=True)
    event_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    available_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    quality_state = Column(String(50), default="valid", nullable=False)  # 'valid', 'stale', 'missing', 'conflicting'
    source_system = Column(String(100), default="lms_sync", nullable=False)
    source_record_ref = Column(String(100), nullable=False)
    source_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "source_system", "source_record_ref", "source_version", name="uq_obs_source"),
    )


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    policy_key = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    definition_json = Column(Text, nullable=False)  # JSON string of rules
    checksum = Column(String(64), nullable=False)  # SHA-256
    status = Column(String(50), default="published", nullable=False)  # 'draft', 'published', 'retired'
    evaluator_version = Column(String(50), default="2.0.0", nullable=False)
    published_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "policy_key", "version", name="uq_inst_policy_version"),
    )


class EvidencePacket(Base):
    __tablename__ = "evidence_packets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    policy_version_id = Column(String(36), ForeignKey("policy_versions.id"), nullable=False)
    as_of_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    digest = Column(String(64), nullable=False)  # SHA-256 of canonical snapshot
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class SignalReview(Base):
    __tablename__ = "signal_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    signal_id = Column(String(36), ForeignKey("signals.id"), unique=True, nullable=False)
    decision = Column(String(50), nullable=False)  # 'approve', 'modify', 'dismiss', 'request_more_data'
    reason_code = Column(String(100), nullable=False)
    selected_intervention_key = Column(String(100), nullable=True)
    reviewed_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class InterventionCatalog(Base):
    __tablename__ = "intervention_catalog"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    intervention_key = Column(String(100), nullable=False)
    domain = Column(String(50), default="academic", nullable=False)
    display_label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_purpose_key = Column(String(100), default="early_warning", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "intervention_key", "version", name="uq_inst_interv_ver"),
    )


class CaseTask(Base):
    __tablename__ = "case_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    domain = Column(String(50), default="academic", nullable=False)  # 'academic', 'mentor', 'counselling'
    generic_label = Column(String(255), nullable=False)
    state = Column(String(50), default="pending", nullable=False)  # 'pending', 'accepted', 'in_progress', 'completed'
    assignee_user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CaseOutcome(Base):
    __tablename__ = "case_outcomes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), unique=True, nullable=False)
    outcome_status = Column(String(50), nullable=False)  # 'helped', 'not_helped', 'mixed', 'unknown'
    rationale = Column(Text, nullable=False)
    evidence_kind = Column(String(100), default="academic_record", nullable=False)
    recorded_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("cases.id"), nullable=False)
    actor_user_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    actor_kind = Column(String(50), default="user", nullable=False)  # 'user', 'system_worker'
    event_type = Column(String(100), nullable=False)
    from_state = Column(String(50), nullable=True)
    to_state = Column(String(50), nullable=True)
    reason_code = Column(String(100), nullable=True)
    prev_hash = Column(String(64), nullable=True)  # Hash of previous event in case chain
    hash = Column(String(64), nullable=False)  # SHA-256(prev_hash || canonical_event)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CounselorCallRequest(Base):
    __tablename__ = "counselor_call_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    preferred_contact_method = Column(String(50), default="voice_call", nullable=False)  # 'voice_call', 'in_person', 'video'
    preferred_time_slot = Column(String(50), default="flexible", nullable=False)  # 'morning', 'afternoon', 'flexible'
    student_notes = Column(Text, nullable=True)
    status = Column(String(50), default="requested", nullable=False)  # 'requested', 'assigned', 'contact_completed', 'closed'
    assigned_counselor_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class PulseQuestionnaire(Base):
    __tablename__ = "pulse_questionnaires"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    version = Column(String(50), default="v1.0-weekly", nullable=False)
    title = Column(String(255), default="Weekly Student Wellbeing Pulse", nullable=False)
    questions_json = Column(Text, nullable=False)  # JSON string of Likert questions
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PulsePeriod(Base):
    __tablename__ = "pulse_periods"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    period_key = Column(String(50), nullable=False)  # e.g., '2026-W44'
    label = Column(String(100), nullable=False)  # e.g., 'Week 44, October 2026'
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "period_key", name="uq_inst_period"),
    )


class PulseSubmission(Base):
    __tablename__ = "pulse_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    period_id = Column(String(36), ForeignKey("pulse_periods.id"), nullable=False)
    questionnaire_version = Column(String(50), default="v1.0-weekly", nullable=False)
    responses_json = Column(Text, nullable=False)  # JSON map of 6 dimension scores (1-5)
    overall_index = Column(Float, nullable=False)  # Computed 0-100 index
    reflection_encrypted = Column(Text, nullable=True)  # Sensitive student text (INV-05)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "period_id", name="uq_student_period_pulse"),
    )


class PointsLedgerEntry(Base):
    __tablename__ = "points_ledger_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    activity_key = Column(String(100), nullable=False)  # 'weekly_pulse', 'verified_learning', etc.
    points = Column(Integer, nullable=False)  # Signed int (+10, -50 for redemption)
    source_ref = Column(String(100), nullable=True)
    idempotency_key = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class RewardCatalogItem(Base):
    __tablename__ = "reward_catalog_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    sku = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="stationery", nullable=False)  # 'digital', 'stationery', 'apparel'
    points_cost = Column(Integer, default=100, nullable=False)
    stock = Column(Integer, default=50, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "sku", name="uq_inst_sku"),
    )


class Redemption(Base):
    __tablename__ = "redemptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("reward_catalog_items.id"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    status = Column(String(50), default="requested", nullable=False)  # 'requested', 'approved', 'fulfilled', 'cancelled'
    idempotency_key = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    document_ref = Column(String(100), nullable=False)  # Unique external reference
    title = Column(String(255), nullable=False)
    doc_type = Column(String(100), default="intervention_plan", nullable=False)  # 'intervention_plan', 'support_summary'
    storage_key = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), nullable=False)  # SHA-256 digest of exact file bytes
    status = Column(String(50), default="finalized", nullable=False)  # 'draft', 'finalized', 'verified_match'
    created_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    finalized_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("institution_id", "document_ref", name="uq_inst_doc_ref"),
    )


class StudentIdentity(Base):
    __tablename__ = "student_identities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("user_profiles.id"), unique=True, nullable=False)
    disha_id = Column(String(50), unique=True, nullable=False)  # 'DISHA-XXXX-XXXX-XXXX'
    display_name = Column(String(255), nullable=False)
    avatar_config_json = Column(Text, nullable=True)  # JSON cosmetic configuration
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)




# =========================================================================
# STUDENT PULSE MODULE ENTITIES (Replacing CLO-based assessments)
# =========================================================================

class PulseQuestionBankItem(Base):
    """Unified Question Bank for Student Pulse across Academic, Feedback, and Wellbeing."""
    __tablename__ = "pulse_question_bank"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    course_id = Column(String(50), nullable=False)  # e.g., 'CS201', 'CS202'
    category = Column(String(50), nullable=False)  # 'ACADEMIC', 'CLASSROOM_FEEDBACK', 'WELLBEING'
    prompt = Column(Text, nullable=False)
    question_type = Column(String(50), default="mcq", nullable=False)  # 'mcq', 'descriptive', 'likert', 'single_choice', 'multi_choice'
    difficulty = Column(String(50), default="Medium", nullable=False)  # 'Easy', 'Medium', 'Hard'
    marks = Column(Float, default=2.0, nullable=False)
    options_json = Column(Text, nullable=True)  # JSON array of choice options
    correct_option = Column(Integer, nullable=True)  # index or key for objective scoring
    correct_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    parameter_tag = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StudentPulseAssignment(Base):
    """Faculty-configured and published Student Pulse assignments with locked randomized questions."""
    __tablename__ = "student_pulse_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    course_id = Column(String(50), nullable=False)
    section_id = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="published", nullable=False)  # 'draft', 'published', 'closed'
    academic_count = Column(Integer, default=5, nullable=False)
    feedback_count = Column(Integer, default=4, nullable=False)
    wellbeing_count = Column(Integer, default=3, nullable=False)
    total_marks = Column(Float, default=15.0, nullable=False)
    selected_question_ids_json = Column(Text, nullable=False)  # JSON array of locked randomized question IDs
    due_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("user_profiles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StudentPulseSubmission(Base):
    """Student answers, auto-graded academic score, and anonymized feedback/wellbeing responses."""
    __tablename__ = "student_pulse_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    pulse_id = Column(String(36), ForeignKey("student_pulse_assignments.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    academic_score = Column(Float, nullable=False)
    academic_max_marks = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    academic_answers_json = Column(Text, nullable=False)
    feedback_answers_json = Column(Text, nullable=False)
    wellbeing_answers_json = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=True, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("pulse_id", "student_id", name="uq_pulse_student_submission"),
    )


class PeerMentorPool(Base):
    """Students in good academic standing who volunteer for subject-specific peer mentoring."""
    __tablename__ = "peer_mentor_pool"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, unique=True)
    eligible_courses_json = Column(Text, nullable=False)  # JSON array of course codes, e.g. ["CS201", "CS202"]
    availability = Column(String(50), default="AVAILABLE", nullable=False)  # 'AVAILABLE', 'BUSY', 'INACTIVE'
    max_capacity = Column(Integer, default=3, nullable=False)
    active_mentees_count = Column(Integer, default=0, nullable=False)
    volunteer_status = Column(String(50), default="ACTIVE_VOLUNTEER", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class PeerMentorRequest(Base):
    """Mentorship offers triggered by academic intervention."""
    __tablename__ = "peer_mentor_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    mentor_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    course_id = Column(String(50), nullable=False)
    status = Column(String(50), default="OFFERED", nullable=False)  # 'OFFERED', 'ACCEPTED', 'DECLINED', 'REASSIGNED'
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)


class CounsellorSupportOffer(Base):
    """Private counselling offers triggered when wellbeing score < 60%."""
    __tablename__ = "counsellor_support_offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    counsellor_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=True)
    status = Column(String(50), default="OFFERED", nullable=False)  # 'OFFERED', 'ACCEPTED', 'DECLINED'
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)


class PulseInterventionRecord(Base):
    """Audit log of interventions evaluated by the Student Pulse Intervention Engine."""
    __tablename__ = "pulse_intervention_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    pulse_id = Column(String(36), ForeignKey("student_pulse_assignments.id"), nullable=False)
    course_id = Column(String(50), nullable=False)
    academic_score = Column(Float, nullable=False)
    feedback_score = Column(Float, nullable=False)
    wellbeing_score = Column(Float, nullable=False)
    academic_status = Column(String(20), nullable=False)  # 'GOOD' | 'LOW'
    feedback_status = Column(String(20), nullable=False)  # 'GOOD' | 'LOW'
    wellbeing_status = Column(String(20), nullable=False)  # 'GOOD' | 'LOW'
    recommended_actions_json = Column(Text, nullable=False)  # JSON array
    status = Column(String(50), default="GENERATED", nullable=False)  # 'GENERATED', 'ACTIONED', 'DISMISSED'
    scoring_version = Column(String(50), default="v1.0-operational", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PulseThresholdConfig(Base):
    """Configurable operational thresholds for category score evaluation."""
    __tablename__ = "pulse_threshold_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(50), nullable=False)  # 'ACADEMIC', 'CLASSROOM_FEEDBACK', 'WELLBEING'
    threshold_percentage = Column(Float, default=60.0, nullable=False)
    version = Column(String(50), default="v1.0-operational", nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

