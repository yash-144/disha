"""Policy engine, wellbeing pulse and rewards ledger

Revision ID: 005_policy_analytics_wellbeing
Revises: 004_counselling_interventions
Create Date: 2026-11-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_policy_analytics_wellbeing'
down_revision = '004_counselling_interventions'
branch_labels = None
depends_on = None

JSONT = sa.JSON().with_variant(postgresql.JSONB(), 'postgresql')
NOW = sa.text('now()')


def _ts(name, nullable=False, default=True):
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable, server_default=NOW if default else None)


def upgrade() -> None:
    # ---- policy ----
    op.create_table(
        'disha_policy_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('definition', JSONT, nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        _ts('created_at'), _ts('updated_at'),
        sa.Column('published_by', sa.String(36), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('campus_id', 'version', name='uq_policy_campus_version'),
    )
    op.create_index('ix_disha_policy_versions_campus_id', 'disha_policy_versions', ['campus_id'])
    op.create_index('ix_disha_policy_versions_status', 'disha_policy_versions', ['status'])
    # At most one active version per campus.
    op.create_index('uq_policy_one_active_per_campus', 'disha_policy_versions', ['campus_id'], unique=True,
                    postgresql_where=sa.text("status = 'active'"), sqlite_where=sa.text("status = 'active'"))

    op.create_table(
        'disha_policy_evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('policy_version_id', sa.String(36), sa.ForeignKey('disha_policy_versions.id'), nullable=False),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('flags_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cases_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_summary', JSONT, nullable=False),
        _ts('created_at'),
    )
    op.create_index('ix_disha_policy_evaluations_campus_id', 'disha_policy_evaluations', ['campus_id'])
    op.create_index('ix_disha_policy_evaluations_policy_version_id', 'disha_policy_evaluations', ['policy_version_id'])
    op.create_index('ix_disha_policy_evaluations_created_at', 'disha_policy_evaluations', ['created_at'])

    op.create_table(
        'disha_policy_decisions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('evaluation_id', sa.String(36), sa.ForeignKey('disha_policy_evaluations.id'), nullable=False),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), nullable=True),
        sa.Column('external_student_ref_hash', sa.String(128), nullable=True),
        sa.Column('course_ref', sa.String(200), nullable=True),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('probability', sa.Float(), nullable=True),
        sa.Column('score_id', sa.String(100), nullable=True),
        sa.Column('decision', sa.String(30), nullable=False),
        sa.Column('reason_code', sa.String(60), nullable=False),
        sa.Column('case_id', sa.String(36), nullable=True),
        sa.Column('signal_id', sa.String(36), nullable=True),
        sa.Column('evidence', JSONT, nullable=True),
        sa.Column('digest', sa.String(64), nullable=True),
        _ts('created_at'),
    )
    for col in ('evaluation_id', 'campus_id', 'student_id', 'case_id', 'created_at'):
        op.create_index(f'ix_disha_policy_decisions_{col}', 'disha_policy_decisions', [col])

    # ---- wellbeing pulse ----
    op.create_table(
        'disha_pulse_questionnaires',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('version_key', sa.String(50), nullable=False),
        sa.Column('questions', JSONT, nullable=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        _ts('created_at'),
        sa.UniqueConstraint('campus_id', 'version_key', name='uq_pulse_q_version'),
    )
    op.create_index('ix_disha_pulse_questionnaires_campus_id', 'disha_pulse_questionnaires', ['campus_id'])

    op.create_table(
        'disha_pulse_periods',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('questionnaire_id', sa.String(36), sa.ForeignKey('disha_pulse_questionnaires.id'), nullable=False),
        sa.Column('label', sa.String(50), nullable=False),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(36), nullable=False),
        _ts('created_at'),
        sa.UniqueConstraint('campus_id', 'label', name='uq_pulse_period_label'),
    )
    op.create_index('ix_disha_pulse_periods_campus_id', 'disha_pulse_periods', ['campus_id'])
    op.create_index('ix_disha_pulse_periods_starts_at', 'disha_pulse_periods', ['starts_at'])

    op.create_table(
        'disha_pulse_submissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('period_id', sa.String(36), sa.ForeignKey('disha_pulse_periods.id'), nullable=False),
        sa.Column('questionnaire_id', sa.String(36), sa.ForeignKey('disha_pulse_questionnaires.id'), nullable=False),
        sa.Column('responses', JSONT, nullable=False),
        sa.Column('dimension_scores', JSONT, nullable=False),
        sa.Column('index_score', sa.Float(), nullable=True),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('reflection_ciphertext', sa.Text(), nullable=True),
        _ts('submitted_at'),
        sa.UniqueConstraint('student_id', 'period_id', name='uq_pulse_student_period'),
    )
    for col in ('campus_id', 'student_id', 'period_id', 'submitted_at'):
        op.create_index(f'ix_disha_pulse_submissions_{col}', 'disha_pulse_submissions', [col])

    # ---- rewards ----
    op.create_table(
        'disha_reward_ledger',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('entry_type', sa.String(20), nullable=False),
        sa.Column('activity_key', sa.String(60), nullable=True),
        sa.Column('source_ref', sa.String(200), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(300), nullable=False),
        sa.Column('reference_id', sa.String(36), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        _ts('created_at'),
        sa.UniqueConstraint('campus_id', 'idempotency_key', name='uq_reward_ledger_idem'),
    )
    for col in ('campus_id', 'student_id', 'created_at'):
        op.create_index(f'ix_disha_reward_ledger_{col}', 'disha_reward_ledger', [col])

    op.create_table(
        'disha_reward_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('cost_points', sa.Integer(), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts('created_at'), _ts('updated_at'),
    )
    op.create_index('ix_disha_reward_items_campus_id', 'disha_reward_items', ['campus_id'])

    op.create_table(
        'disha_reward_redemptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campus_id', sa.String(36), nullable=False),
        sa.Column('student_id', sa.String(36), sa.ForeignKey('disha_roster.id'), nullable=False),
        sa.Column('item_id', sa.String(36), sa.ForeignKey('disha_reward_items.id'), nullable=False),
        sa.Column('cost_points', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='requested'),
        sa.Column('idempotency_key', sa.String(300), nullable=False),
        sa.Column('handled_by', sa.String(36), nullable=True),
        sa.Column('handled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        _ts('created_at'), _ts('updated_at'),
        sa.UniqueConstraint('campus_id', 'student_id', 'idempotency_key', name='uq_redemption_idem'),
    )
    for col in ('campus_id', 'student_id', 'item_id', 'status'):
        op.create_index(f'ix_disha_reward_redemptions_{col}', 'disha_reward_redemptions', [col])

    # Database-level append-only guarantee for the points ledger (PTS-01).
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("""
            CREATE FUNCTION disha_reward_ledger_immutable() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'disha_reward_ledger is append-only'; END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER disha_reward_ledger_no_change BEFORE UPDATE OR DELETE ON disha_reward_ledger
            FOR EACH ROW EXECUTE FUNCTION disha_reward_ledger_immutable();
        """)


def downgrade() -> None:
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP TRIGGER IF EXISTS disha_reward_ledger_no_change ON disha_reward_ledger")
        op.execute("DROP FUNCTION IF EXISTS disha_reward_ledger_immutable()")
    for t in ('disha_reward_redemptions', 'disha_reward_items', 'disha_reward_ledger',
              'disha_pulse_submissions', 'disha_pulse_periods', 'disha_pulse_questionnaires',
              'disha_policy_decisions', 'disha_policy_evaluations', 'disha_policy_versions'):
        op.drop_table(t)
