"""Student and Faculty module initial schema

Revision ID: 002_student_faculty_module
Revises: 001_counsellor_module
Create Date: 2026-11-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '002_student_faculty_module'
down_revision = '001_counsellor_module'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Extend disha_roster
    op.add_column('disha_roster', sa.Column('user_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=True))
    op.add_column('disha_roster', sa.Column('cohort_code', sa.String(100), nullable=True))
    op.add_column('disha_roster', sa.Column('enrollment_status', sa.String(50), nullable=False, server_default='active'))
    op.add_column('disha_roster', sa.Column('attendance_rate', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('disha_roster', sa.Column('quiz_score_avg', sa.Float(), nullable=False, server_default='0.0'))
    op.create_index('ix_disha_roster_user_id', 'disha_roster', ['user_id'], unique=True)
    op.create_index('ix_disha_roster_cohort_code', 'disha_roster', ['cohort_code'])

    # 2. disha_faculty_profiles
    op.create_table(
        'disha_faculty_profiles',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('avatar', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', name='uq_disha_faculty_user_id'),
    )
    op.create_index('ix_disha_faculty_profiles_user_id', 'disha_faculty_profiles', ['user_id'])
    op.create_index('ix_disha_faculty_profiles_campus_id', 'disha_faculty_profiles', ['campus_id'])

    # 3. disha_courses
    op.create_table(
        'disha_courses',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, server_default='Computer Science & IT'),
        sa.Column('credits', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('semester', sa.String(50), nullable=False, server_default='Fall 2025'),
        sa.Column('primary_faculty_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_courses_campus_id', 'disha_courses', ['campus_id'])
    op.create_index('ix_disha_courses_code', 'disha_courses', ['code'])
    op.create_index('ix_disha_courses_primary_faculty_id', 'disha_courses', ['primary_faculty_id'])

    # 4. disha_course_sections
    op.create_table(
        'disha_course_sections',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('disha_courses.id'), nullable=False),
        sa.Column('faculty_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('section_code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('term', sa.String(100), nullable=False, server_default='July - Dec 2025'),
        sa.Column('access_code', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False, server_default='Computer Science'),
        sa.Column('color', sa.String(50), nullable=False, server_default='bg-blue-600'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('access_code', name='uq_disha_sections_access_code'),
    )
    op.create_index('ix_disha_course_sections_campus_id', 'disha_course_sections', ['campus_id'])
    op.create_index('ix_disha_course_sections_course_id', 'disha_course_sections', ['course_id'])
    op.create_index('ix_disha_course_sections_faculty_id', 'disha_course_sections', ['faculty_id'])

    # 5. disha_course_enrollments
    op.create_table(
        'disha_course_enrollments',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('section_id', sa.String(36), sa.ForeignKey('disha_course_sections.id'), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='enrolled'),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('section_id', 'student_id', name='uq_disha_enrollment_sec_stu'),
    )
    op.create_index('ix_disha_course_enrollments_campus_id', 'disha_course_enrollments', ['campus_id'])
    op.create_index('ix_disha_course_enrollments_section_id', 'disha_course_enrollments', ['section_id'])
    op.create_index('ix_disha_course_enrollments_student_id', 'disha_course_enrollments', ['student_id'])

    # 6. disha_attendance_records
    op.create_table(
        'disha_attendance_records',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('section_id', sa.String(36), sa.ForeignKey('disha_course_sections.id'), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('date', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('recorded_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_attendance_records_campus_id', 'disha_attendance_records', ['campus_id'])
    op.create_index('ix_disha_attendance_records_section_id', 'disha_attendance_records', ['section_id'])
    op.create_index('ix_disha_attendance_records_student_id', 'disha_attendance_records', ['student_id'])
    op.create_index('ix_disha_attendance_records_date', 'disha_attendance_records', ['date'])

    # 7. disha_assessments
    op.create_table(
        'disha_assessments',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('section_id', sa.String(36), sa.ForeignKey('disha_course_sections.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('assessment_type', sa.String(50), nullable=False, server_default='quiz'),
        sa.Column('total_marks', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('clo_code', sa.String(50), nullable=True, server_default='CLO-1'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_assessments_campus_id', 'disha_assessments', ['campus_id'])
    op.create_index('ix_disha_assessments_section_id', 'disha_assessments', ['section_id'])

    # 8. disha_assessment_submissions
    op.create_table(
        'disha_assessment_submissions',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('assessment_id', sa.String(36), sa.ForeignKey('disha_assessments.id'), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('graded_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('assessment_id', 'student_id', name='uq_disha_sub_assessment_stu'),
    )
    op.create_index('ix_disha_assessment_submissions_campus_id', 'disha_assessment_submissions', ['campus_id'])
    op.create_index('ix_disha_assessment_submissions_assessment_id', 'disha_assessment_submissions', ['assessment_id'])
    op.create_index('ix_disha_assessment_submissions_student_id', 'disha_assessment_submissions', ['student_id'])

    # 9. disha_support_requests
    op.create_table(
        'disha_support_requests',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('faculty_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('course_id', sa.String(36), sa.ForeignKey('disha_courses.id'), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('preferred_slot', sa.String(100), nullable=False),
        sa.Column('student_note', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='requested'),
        sa.Column('faculty_response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_support_requests_campus_id', 'disha_support_requests', ['campus_id'])
    op.create_index('ix_disha_support_requests_student_id', 'disha_support_requests', ['student_id'])
    op.create_index('ix_disha_support_requests_faculty_id', 'disha_support_requests', ['faculty_id'])

    # 10. disha_signals
    op.create_table(
        'disha_signals',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('rule_key', sa.String(100), nullable=False),
        sa.Column('result', sa.String(50), nullable=False, server_default='attention_suggested'),
        sa.Column('ml_risk_probability', sa.Float(), nullable=True),
        sa.Column('ml_tier', sa.String(50), nullable=True),
        sa.Column('evidence_snapshot', sa.Text(), nullable=True),
        sa.Column('reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reviewed_decision', sa.String(50), nullable=True),
        sa.Column('review_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_signals_campus_id', 'disha_signals', ['campus_id'])
    op.create_index('ix_disha_signals_student_id', 'disha_signals', ['student_id'])

    # 11. Add originating_signal_id to disha_cases
    op.add_column('disha_cases', sa.Column('originating_signal_id', sa.String(36), sa.ForeignKey('disha_signals.id'), nullable=True))
    op.create_unique_constraint('uq_disha_cases_originating_signal', 'disha_cases', ['originating_signal_id'])


def downgrade() -> None:
    op.drop_constraint('uq_disha_cases_originating_signal', 'disha_cases', type_='unique')
    op.drop_column('disha_cases', 'originating_signal_id')
    op.drop_table('disha_signals')
    op.drop_table('disha_support_requests')
    op.drop_table('disha_assessment_submissions')
    op.drop_table('disha_assessments')
    op.drop_table('disha_attendance_records')
    op.drop_table('disha_course_enrollments')
    op.drop_table('disha_course_sections')
    op.drop_table('disha_courses')
    op.drop_table('disha_faculty_profiles')
    op.drop_index('ix_disha_roster_cohort_code', table_name='disha_roster')
    op.drop_index('ix_disha_roster_user_id', table_name='disha_roster')
    op.drop_column('disha_roster', 'quiz_score_avg')
    op.drop_column('disha_roster', 'attendance_rate')
    op.drop_column('disha_roster', 'enrollment_status')
    op.drop_column('disha_roster', 'cohort_code')
    op.drop_column('disha_roster', 'user_id')
