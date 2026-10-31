"""Canonical-table storage for the rolling risk model.

One `ImportBatch` per upload. Every canonical row carries `campus_id` and `batch_id`; a committed batch is
"active" until a later batch covering the same terms supersedes it. Student identifiers are kept exactly as the
campus supplied them (`student_ref`); `roster_student_id` links to the roster when a student with the same
`student_uid` exists in that campus (unlinked students are still scored).
"""
import uuid

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.shared.utils import utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")

BATCH_VALIDATED = "validated"      # dry run: checked, nothing stored
BATCH_COMMITTED = "committed"      # rows stored and active
BATCH_SUPERSEDED = "superseded"    # replaced by a later batch covering the same terms
BATCH_REJECTED = "rejected"        # validation failed, nothing stored
BATCH_FAILED = "failed"            # unexpected error while storing

TABLE_NAMES = ("students", "enrolments", "assessments", "results", "activity", "withdrawals")


def _id() -> str:
    return str(uuid.uuid4())


class ImportBatch(Base):
    __tablename__ = "disha_import_batches"
    __table_args__ = (Index("ix_disha_import_batches_campus_sha", "campus_id", "file_sha256"),)

    id = Column(String(36), primary_key=True, default=_id)
    campus_id = Column(String(36), nullable=False, index=True)
    uploaded_by = Column(String(36), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    source_files = Column(JSONType, nullable=False, default=list)       # [{table, filename, bytes, sha256}]
    file_sha256 = Column(String(64), nullable=False)                    # sha256 over the per-file digests (idempotency key)
    row_counts = Column(JSONType, nullable=False, default=dict)         # {table: n}
    term_ids = Column(JSONType, nullable=False, default=list)
    validation_errors = Column(JSONType, nullable=False, default=list)  # [{code, table, message, count, sample}]
    warnings = Column(JSONType, nullable=False, default=list)
    linked_students = Column(Integer, nullable=False, default=0)
    unlinked_students = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=True)


class MlStudent(Base):
    __tablename__ = "disha_ml_students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)
    roster_student_id = Column(String(36), nullable=True)
    program_level = Column(String(20), nullable=True)
    year_of_study = Column(Float, nullable=True)
    tenth_pct = Column(Float, nullable=True)
    twelfth_pct = Column(Float, nullable=True)
    entrance_pct = Column(Float, nullable=True)
    prior_education_ord = Column(Float, nullable=True)
    # fairness audit only, never model inputs
    gender = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    imd_band = Column(String(50), nullable=True)
    disability = Column(String(50), nullable=True)
    age_band = Column(String(50), nullable=True)


class MlEnrolment(Base):
    __tablename__ = "disha_ml_enrolments"
    __table_args__ = (UniqueConstraint("batch_id", "student_ref", "course_id", "term_id", name="uq_ml_enrolment"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)
    roster_student_id = Column(String(36), nullable=True)
    term_id = Column(String(100), nullable=False)
    course_id = Column(String(100), nullable=False)
    term_length_days = Column(Float, nullable=False)
    term_start = Column(String(32), nullable=True)   # ISO date as supplied
    outcome = Column(String(20), nullable=True)
    prev_attempts = Column(Float, nullable=True)
    credit_load = Column(Float, nullable=True)
    section = Column(String(100), nullable=True)


class MlAssessment(Base):
    __tablename__ = "disha_ml_assessments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    assessment_id = Column(String(100), nullable=False)
    course_id = Column(String(100), nullable=False)
    term_id = Column(String(100), nullable=False)
    due_day = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)
    type = Column(String(50), nullable=True)


class MlResult(Base):
    __tablename__ = "disha_ml_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)
    assessment_id = Column(String(100), nullable=False)
    submitted_day = Column(Float, nullable=False)
    score_pct = Column(Float, nullable=True)


class MlActivity(Base):
    __tablename__ = "disha_ml_activity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)
    course_id = Column(String(100), nullable=False)
    term_id = Column(String(100), nullable=False)
    day = Column(Float, nullable=False)
    count = Column(Float, nullable=False)


class MlWithdrawal(Base):
    __tablename__ = "disha_ml_withdrawals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campus_id = Column(String(36), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("disha_import_batches.id"), nullable=False, index=True)
    student_ref = Column(String(200), nullable=False)
    course_id = Column(String(100), nullable=False)
    term_id = Column(String(100), nullable=False)
    day = Column(Float, nullable=False)


ROW_MODELS = {
    "students": MlStudent, "enrolments": MlEnrolment, "assessments": MlAssessment,
    "results": MlResult, "activity": MlActivity, "withdrawals": MlWithdrawal,
}
