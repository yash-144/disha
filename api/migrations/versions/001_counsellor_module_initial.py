"""Counsellor module initial schema

Revision ID: 001_counsellor_module
Revises: 
Create Date: 2026-10-31

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_counsellor_module'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. disha_identity (users)
    op.create_table(
        'disha_identity',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('hashed_password', sa.String(200), nullable=False),
        sa.Column('full_name', sa.String(300), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_identity_email', 'disha_identity', ['email'], unique=True)

    # 2. disha_memberships
    op.create_table(
        'disha_memberships',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_memberships_user_id', 'disha_memberships', ['user_id'])
    op.create_index('ix_disha_memberships_campus_id', 'disha_memberships', ['campus_id'])

    # 3. disha_roster (students)
    op.create_table(
        'disha_roster',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_uid', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(300), nullable=False),
        sa.Column('email', sa.String(320), nullable=True),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('course', sa.String(200), nullable=True),
        sa.Column('academic_year', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_roster_campus_id', 'disha_roster', ['campus_id'])
    op.create_index('ix_disha_roster_student_uid', 'disha_roster', ['student_uid'])

    # 4. disha_observations
    op.create_table(
        'disha_observations',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('domain', sa.String(50), nullable=False),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_observations_student_id', 'disha_observations', ['student_id'])
    op.create_index('ix_disha_observations_campus_id', 'disha_observations', ['campus_id'])

    # 5. disha_counsellor_profiles
    op.create_table(
        'disha_counsellor_profiles',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('specialisation', sa.String(300), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', name='uq_counsellor_profiles_user_id'),
    )
    op.create_index('ix_disha_counsellor_profiles_user_id', 'disha_counsellor_profiles', ['user_id'])
    op.create_index('ix_disha_counsellor_profiles_campus_id', 'disha_counsellor_profiles', ['campus_id'])

    # 6. disha_counsellor_assignments
    op.create_table(
        'disha_counsellor_assignments',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('counsellor_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_counsellor_assignments_counsellor_id', 'disha_counsellor_assignments', ['counsellor_id'])
    op.create_index('ix_disha_counsellor_assignments_student_id', 'disha_counsellor_assignments', ['student_id'])
    op.create_index('ix_disha_counsellor_assignments_campus_id', 'disha_counsellor_assignments', ['campus_id'])

    # 7. disha_cases
    op.create_table(
        'disha_cases',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('assigned_counsellor_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='new'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_cases_campus_id', 'disha_cases', ['campus_id'])
    op.create_index('ix_disha_cases_student_id', 'disha_cases', ['student_id'])
    op.create_index('ix_disha_cases_assigned_counsellor_id', 'disha_cases', ['assigned_counsellor_id'])
    op.create_index('ix_disha_cases_status', 'disha_cases', ['status'])

    # 8. disha_case_notes
    op.create_table(
        'disha_case_notes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('author_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_case_notes_case_id', 'disha_case_notes', ['case_id'])
    op.create_index('ix_disha_case_notes_campus_id', 'disha_case_notes', ['campus_id'])

    # 9. disha_case_events
    op.create_table(
        'disha_case_events',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_case_events_case_id', 'disha_case_events', ['case_id'])
    op.create_index('ix_disha_case_events_campus_id', 'disha_case_events', ['campus_id'])

    # 10. disha_intervention_catalogue
    op.create_table(
        'disha_intervention_catalogue',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('name', name='uq_intervention_catalogue_name'),
    )

    # 11. disha_interventions
    op.create_table(
        'disha_interventions',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('catalogue_id', sa.String(36), sa.ForeignKey('disha_intervention_catalogue.id'), nullable=False),
        sa.Column('counsellor_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('progress', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_interventions_case_id', 'disha_interventions', ['case_id'])
    op.create_index('ix_disha_interventions_campus_id', 'disha_interventions', ['campus_id'])

    # 12. disha_intervention_outcomes
    op.create_table(
        'disha_intervention_outcomes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('intervention_id', sa.String(36), sa.ForeignKey('disha_interventions.id'), nullable=False),
        sa.Column('counsellor_id', sa.String(36), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('completion_status', sa.String(50), nullable=False),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('intervention_id', name='uq_intervention_outcomes_intervention_id'),
    )
    op.create_index('ix_disha_intervention_outcomes_case_id', 'disha_intervention_outcomes', ['case_id'])

    # 13. disha_followups
    op.create_table(
        'disha_followups',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('counsellor_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='scheduled'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_followups_case_id', 'disha_followups', ['case_id'])
    op.create_index('ix_disha_followups_counsellor_id', 'disha_followups', ['counsellor_id'])
    op.create_index('ix_disha_followups_campus_id', 'disha_followups', ['campus_id'])

    # 14. disha_followup_notes
    op.create_table(
        'disha_followup_notes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('followup_id', sa.String(36), sa.ForeignKey('disha_followups.id'), nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=False),
        sa.Column('author_id', sa.String(36), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_followup_notes_followup_id', 'disha_followup_notes', ['followup_id'])
    op.create_index('ix_disha_followup_notes_case_id', 'disha_followup_notes', ['case_id'])

    # 15. disha_notifications
    op.create_table(
        'disha_notifications',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('recipient_id', sa.String(36), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('notification_type', sa.String(100), nullable=False),
        sa.Column('reference_id', sa.String(36), nullable=True),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('idempotency_key', sa.String(200), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_notifications_recipient_id', 'disha_notifications', ['recipient_id'])
    op.create_index('ix_disha_notifications_campus_id', 'disha_notifications', ['campus_id'])
    op.create_index('ix_disha_notifications_idempotency_key', 'disha_notifications', ['idempotency_key'], unique=True)

    # 16. disha_audit_events
    op.create_table(
        'disha_audit_events',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('correlation_id', sa.String(36), nullable=True),
        sa.Column('prev_hash', sa.String(64), nullable=True),
        sa.Column('event_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_disha_audit_events_actor_id', 'disha_audit_events', ['actor_id'])
    op.create_index('ix_disha_audit_events_campus_id', 'disha_audit_events', ['campus_id'])
    op.create_index('ix_disha_audit_events_entity_id', 'disha_audit_events', ['entity_id'])

    # Seed intervention catalogue with some defaults
    op.execute("""
        INSERT INTO disha_intervention_catalogue (id, name, description, category, is_active, created_at)
        VALUES
            ('cat-001-academic-support', 'Academic Support Session', 'One-on-one academic support and guidance session', 'academic', true, now()),
            ('cat-002-counselling-session', 'Counselling Session', 'Individual counselling and emotional support session', 'counselling', true, now()),
            ('cat-003-peer-mentoring', 'Peer Mentoring', 'Connect student with trained peer mentor', 'peer', true, now()),
            ('cat-004-faculty-referral', 'Faculty Referral', 'Refer student to faculty advisor for academic guidance', 'academic', true, now()),
            ('cat-005-wellbeing-check', 'Wellbeing Check-in', 'Regular wellbeing check-in and monitoring', 'wellbeing', true, now()),
            ('cat-006-attendance-intervention', 'Attendance Intervention', 'Targeted intervention for attendance issues', 'attendance', true, now()),
            ('cat-007-financial-guidance', 'Financial Guidance', 'Connect student with financial aid resources', 'financial', true, now()),
            ('cat-008-career-counselling', 'Career Counselling', 'Career guidance and planning session', 'career', true, now())
    """)


def downgrade() -> None:
    op.drop_table('disha_audit_events')
    op.drop_table('disha_notifications')
    op.drop_table('disha_followup_notes')
    op.drop_table('disha_followups')
    op.drop_table('disha_intervention_outcomes')
    op.drop_table('disha_interventions')
    op.drop_table('disha_intervention_catalogue')
    op.drop_table('disha_case_events')
    op.drop_table('disha_case_notes')
    op.drop_table('disha_cases')
    op.drop_table('disha_counsellor_assignments')
    op.drop_table('disha_counsellor_profiles')
    op.drop_table('disha_observations')
    op.drop_table('disha_roster')
    op.drop_table('disha_memberships')
    op.drop_table('disha_identity')
