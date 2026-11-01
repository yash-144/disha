"""Counselling sessions and notes, notification outbox, campus settings and invitations, escalation columns

Revision ID: 004_counselling_interventions
Revises: 003_ml_pipeline
Create Date: 2026-11-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_counselling_interventions'
down_revision = '003_ml_pipeline'
branch_labels = None
depends_on = None

JSON = postgresql.JSONB()


def _ts(name, nullable=False, default=True):
    return sa.Column(
        name, sa.DateTime(timezone=True), nullable=nullable,
        server_default=sa.text('now()') if default else None,
    )


def upgrade() -> None:
    # --- escalation columns on cases (ESC-02) ---
    op.add_column('disha_cases', sa.Column('deadline_version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('disha_cases', sa.Column('escalated_deadline_version', sa.Integer(), nullable=True))
    op.add_column('disha_cases', sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('disha_cases', _ts('escalated_at', nullable=True, default=False))

    # --- follow-ups: type, contact status, proof, escalation marker ---
    op.add_column('disha_followups', sa.Column('follow_up_type', sa.String(50), nullable=False, server_default='follow_up_check'))
    op.add_column('disha_followups', sa.Column('contact_status', sa.String(30), nullable=True))
    op.add_column('disha_followups', sa.Column('proof_kind', sa.String(50), nullable=True))
    op.add_column('disha_followups', _ts('escalated_at', nullable=True, default=False))
    op.create_index('ix_disha_followups_status_scheduled', 'disha_followups', ['status', 'scheduled_at'])

    # --- intervention catalogue becomes campus-scoped (NULL campus = platform-wide) ---
    op.add_column('disha_intervention_catalogue', sa.Column('campus_id', sa.String(36), nullable=True))
    op.create_index('ix_disha_intervention_catalogue_campus_id', 'disha_intervention_catalogue', ['campus_id'])
    op.drop_constraint('uq_intervention_catalogue_name', 'disha_intervention_catalogue', type_='unique')
    op.create_unique_constraint('uq_intervention_catalogue_campus_name', 'disha_intervention_catalogue', ['campus_id', 'name'])
    op.create_index(
        'uq_intervention_catalogue_platform_name', 'disha_intervention_catalogue', ['name'],
        unique=True, postgresql_where=sa.text('campus_id IS NULL'),
    )

    # --- counsellor profile ---
    op.add_column('disha_counsellor_profiles', sa.Column('designation', sa.String(200), nullable=True))
    op.add_column('disha_counsellor_profiles', sa.Column('phone', sa.String(40), nullable=True))
    op.add_column('disha_counsellor_profiles', sa.Column('availability_status', sa.String(30), nullable=False, server_default='available'))

    # --- campuses and invitations ---
    op.create_table(
        'disha_campuses',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', JSON, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by', sa.String(36), nullable=True),
        _ts('created_at'),
        _ts('updated_at'),
        sa.UniqueConstraint('code', name='uq_disha_campuses_code'),
    )
    op.create_table(
        'disha_membership_invites',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('department', sa.String(200), nullable=True),
        _ts('expires_at', default=False),
        _ts('accepted_at', nullable=True, default=False),
        sa.Column('accepted_by', sa.String(36), nullable=True),
        _ts('revoked_at', nullable=True, default=False),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        _ts('created_at'),
    )
    op.create_index('ix_disha_membership_invites_campus_id', 'disha_membership_invites', ['campus_id'])
    op.create_index('ix_disha_membership_invites_campus_email', 'disha_membership_invites', ['campus_id', 'email'])
    op.create_index('ix_disha_membership_invites_email', 'disha_membership_invites', ['email'])

    # --- counselling sessions and confidential notes ---
    op.create_table(
        'disha_counselling_sessions',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=True),
        sa.Column('counsellor_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        _ts('scheduled_at', default=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='45'),
        sa.Column('mode', sa.String(30), nullable=False, server_default='in_person'),
        sa.Column('location', sa.String(300), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='scheduled'),
        sa.Column('cancel_reason', sa.String(500), nullable=True),
        _ts('completed_at', nullable=True, default=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        _ts('created_at'),
        _ts('updated_at'),
    )
    op.create_index('ix_disha_counselling_sessions_campus_id', 'disha_counselling_sessions', ['campus_id'])
    op.create_index('ix_disha_counselling_sessions_student_id', 'disha_counselling_sessions', ['student_id'])
    op.create_index('ix_disha_counselling_sessions_case_id', 'disha_counselling_sessions', ['case_id'])
    op.create_index('ix_disha_counselling_sessions_status', 'disha_counselling_sessions', ['status'])
    op.create_index('ix_disha_counselling_sessions_counsellor_time', 'disha_counselling_sessions', ['counsellor_id', 'scheduled_at'])

    op.create_table(
        'disha_counselling_notes',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('disha_cases.id'), nullable=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('disha_counselling_sessions.id'), nullable=True),
        sa.Column('author_id', sa.String(36), sa.ForeignKey('disha_identity.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        _ts('created_at'),
    )
    op.create_index('ix_disha_counselling_notes_campus_id', 'disha_counselling_notes', ['campus_id'])
    op.create_index('ix_disha_counselling_notes_student_id', 'disha_counselling_notes', ['student_id'])
    op.create_index('ix_disha_counselling_notes_case_id', 'disha_counselling_notes', ['case_id'])
    op.create_index('ix_disha_counselling_notes_author_id', 'disha_counselling_notes', ['author_id'])

    # --- notification outbox ---
    op.create_table(
        'disha_notification_outbox',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=True),
        sa.Column('recipient_id', sa.String(36), nullable=False),
        sa.Column('adapter_key', sa.String(50), nullable=False, server_default='in_app'),
        sa.Column('template_key', sa.String(100), nullable=False),
        sa.Column('safe_payload', JSON, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        _ts('next_attempt_at'),
        sa.Column('last_error_code', sa.String(100), nullable=True),
        sa.Column('idempotency_key', sa.String(250), nullable=False),
        _ts('sent_at', nullable=True, default=False),
        _ts('created_at'),
        sa.UniqueConstraint('idempotency_key', name='uq_disha_notification_outbox_idempotency_key'),
    )
    op.create_index('ix_disha_notification_outbox_campus_id', 'disha_notification_outbox', ['campus_id'])
    op.create_index('ix_disha_notification_outbox_case_id', 'disha_notification_outbox', ['case_id'])
    op.create_index('ix_disha_notification_outbox_recipient_id', 'disha_notification_outbox', ['recipient_id'])
    op.create_index('ix_disha_notification_outbox_status_next', 'disha_notification_outbox', ['status', 'next_attempt_at'])

    op.create_table(
        'disha_outbox_delivery_attempts',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('outbox_id', sa.String(36), sa.ForeignKey('disha_notification_outbox.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('adapter_key', sa.String(50), nullable=False),
        sa.Column('outcome', sa.String(30), nullable=False),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('provider_message_id', sa.String(200), nullable=True),
        _ts('attempted_at'),
    )
    op.create_index('ix_disha_outbox_delivery_attempts_outbox_id', 'disha_outbox_delivery_attempts', ['outbox_id'])

    # --- stored-response idempotency ---
    op.create_table(
        'disha_idempotency_keys',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('key', sa.String(200), nullable=False),
        sa.Column('scope', sa.String(100), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('response_body', JSON, nullable=True),
        _ts('created_at'),
        sa.UniqueConstraint('campus_id', 'actor_id', 'key', name='uq_idempotency_campus_actor_key'),
    )
    op.create_index('ix_disha_idempotency_keys_campus_id', 'disha_idempotency_keys', ['campus_id'])


def downgrade() -> None:
    op.drop_table('disha_idempotency_keys')
    op.drop_table('disha_outbox_delivery_attempts')
    op.drop_table('disha_notification_outbox')
    op.drop_table('disha_counselling_notes')
    op.drop_table('disha_counselling_sessions')
    op.drop_table('disha_membership_invites')
    op.drop_table('disha_campuses')

    op.drop_column('disha_counsellor_profiles', 'availability_status')
    op.drop_column('disha_counsellor_profiles', 'phone')
    op.drop_column('disha_counsellor_profiles', 'designation')

    op.drop_index('uq_intervention_catalogue_platform_name', table_name='disha_intervention_catalogue')
    op.drop_constraint('uq_intervention_catalogue_campus_name', 'disha_intervention_catalogue', type_='unique')
    op.create_unique_constraint('uq_intervention_catalogue_name', 'disha_intervention_catalogue', ['name'])
    op.drop_index('ix_disha_intervention_catalogue_campus_id', table_name='disha_intervention_catalogue')
    op.drop_column('disha_intervention_catalogue', 'campus_id')

    op.drop_index('ix_disha_followups_status_scheduled', table_name='disha_followups')
    op.drop_column('disha_followups', 'escalated_at')
    op.drop_column('disha_followups', 'proof_kind')
    op.drop_column('disha_followups', 'contact_status')
    op.drop_column('disha_followups', 'follow_up_type')

    op.drop_column('disha_cases', 'escalated_at')
    op.drop_column('disha_cases', 'escalation_level')
    op.drop_column('disha_cases', 'escalated_deadline_version')
    op.drop_column('disha_cases', 'deadline_version')
