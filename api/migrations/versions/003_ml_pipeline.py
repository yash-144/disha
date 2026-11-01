"""ML pipeline: canonical-table storage, import batches, scoring runs and risk scores

Revision ID: 003_ml_pipeline
Revises: 002_student_faculty_module
Create Date: 2026-11-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_ml_pipeline'
down_revision = '002_student_faculty_module'
branch_labels = None
depends_on = None


def _json():
    return sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')


def _row_table(name, *cols):
    op.create_table(
        name,
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('batch_id', sa.String(36), sa.ForeignKey('disha_import_batches.id'), nullable=False),
        *cols,
    )
    op.create_index(f'ix_{name}_campus_id', name, ['campus_id'])
    op.create_index(f'ix_{name}_batch_id', name, ['batch_id'])


def upgrade() -> None:
    op.create_table(
        'disha_import_batches',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('uploaded_by', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('source_files', _json(), nullable=False),
        sa.Column('file_sha256', sa.String(64), nullable=False),
        sa.Column('row_counts', _json(), nullable=False),
        sa.Column('term_ids', _json(), nullable=False),
        sa.Column('validation_errors', _json(), nullable=False),
        sa.Column('warnings', _json(), nullable=False),
        sa.Column('linked_students', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unlinked_students', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_disha_import_batches_campus_id', 'disha_import_batches', ['campus_id'])
    op.create_index('ix_disha_import_batches_status', 'disha_import_batches', ['status'])
    op.create_index('ix_disha_import_batches_campus_sha', 'disha_import_batches', ['campus_id', 'file_sha256'])

    _row_table(
        'disha_ml_students',
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('roster_student_id', sa.String(36), nullable=True),
        sa.Column('program_level', sa.String(20), nullable=True),
        sa.Column('year_of_study', sa.Float(), nullable=True),
        sa.Column('tenth_pct', sa.Float(), nullable=True),
        sa.Column('twelfth_pct', sa.Float(), nullable=True),
        sa.Column('entrance_pct', sa.Float(), nullable=True),
        sa.Column('prior_education_ord', sa.Float(), nullable=True),
        sa.Column('gender', sa.String(50), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('imd_band', sa.String(50), nullable=True),
        sa.Column('disability', sa.String(50), nullable=True),
        sa.Column('age_band', sa.String(50), nullable=True),
    )
    _row_table(
        'disha_ml_enrolments',
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('roster_student_id', sa.String(36), nullable=True),
        sa.Column('term_id', sa.String(100), nullable=False),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('term_length_days', sa.Float(), nullable=False),
        sa.Column('term_start', sa.String(32), nullable=True),
        sa.Column('outcome', sa.String(20), nullable=True),
        sa.Column('prev_attempts', sa.Float(), nullable=True),
        sa.Column('credit_load', sa.Float(), nullable=True),
        sa.Column('section', sa.String(100), nullable=True),
        sa.UniqueConstraint('batch_id', 'student_ref', 'course_id', 'term_id', name='uq_ml_enrolment'),
    )
    _row_table(
        'disha_ml_assessments',
        sa.Column('assessment_id', sa.String(100), nullable=False),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('term_id', sa.String(100), nullable=False),
        sa.Column('due_day', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
    )
    _row_table(
        'disha_ml_results',
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('assessment_id', sa.String(100), nullable=False),
        sa.Column('submitted_day', sa.Float(), nullable=False),
        sa.Column('score_pct', sa.Float(), nullable=True),
    )
    _row_table(
        'disha_ml_activity',
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('term_id', sa.String(100), nullable=False),
        sa.Column('day', sa.Float(), nullable=False),
        sa.Column('count', sa.Float(), nullable=False),
    )
    _row_table(
        'disha_ml_withdrawals',
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('term_id', sa.String(100), nullable=False),
        sa.Column('day', sa.Float(), nullable=False),
    )

    op.create_table(
        'disha_ml_runs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('triggered_by', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('term_id', sa.String(100), nullable=True),
        sa.Column('as_of_day', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.Column('bundle_sha256', sa.String(64), nullable=True),
        sa.Column('schema_version', sa.String(20), nullable=True),
        sa.Column('batch_ids', _json(), nullable=False),
        sa.Column('n_scored', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tier_counts', _json(), nullable=False),
        sa.Column('cohorts', _json(), nullable=True),
        sa.Column('data_drift', _json(), nullable=True),
        sa.Column('model_info', _json(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_disha_ml_runs_campus_id', 'disha_ml_runs', ['campus_id'])
    op.create_index('ix_disha_ml_runs_status', 'disha_ml_runs', ['status'])

    op.create_table(
        'disha_ml_scores',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(36), sa.ForeignKey('disha_ml_runs.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_ref', sa.String(200), nullable=False),
        sa.Column('external_student_ref_hash', sa.String(40), nullable=False),
        sa.Column('student_id', sa.String(36), nullable=True),
        sa.Column('course_id', sa.String(100), nullable=False),
        sa.Column('term_id', sa.String(100), nullable=False),
        sa.Column('as_of_day', sa.Integer(), nullable=False),
        sa.Column('as_of_date', sa.String(10), nullable=True),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('tier', sa.String(10), nullable=False),
        sa.Column('signal', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('previous_probability', sa.Float(), nullable=True),
        sa.Column('previous_tier', sa.String(10), nullable=True),
        sa.Column('direction', sa.String(10), nullable=True),
        sa.Column('reasons', _json(), nullable=False),
        sa.Column('insight', _json(), nullable=False),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_ml_scores_run_id', 'disha_ml_scores', ['run_id'])
    op.create_index('ix_disha_ml_scores_campus_id', 'disha_ml_scores', ['campus_id'])
    op.create_index('ix_disha_ml_scores_student_id', 'disha_ml_scores', ['student_id'])
    op.create_index('ix_disha_ml_scores_run_tier', 'disha_ml_scores', ['run_id', 'tier'])
    op.create_index('ix_disha_ml_scores_campus_hash', 'disha_ml_scores', ['campus_id', 'external_student_ref_hash'])


def downgrade() -> None:
    for t in ('disha_ml_scores', 'disha_ml_runs', 'disha_ml_withdrawals', 'disha_ml_activity', 'disha_ml_results',
              'disha_ml_assessments', 'disha_ml_enrolments', 'disha_ml_students', 'disha_import_batches'):
        op.drop_table(t)
