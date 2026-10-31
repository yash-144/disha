"""case lifecycle, outbox and campus membership

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None

TS = sa.DateTime(timezone=True)


def _pk():
    return sa.Column("id", sa.String(36), primary_key=True)


def upgrade():
    op.create_table(
        "disha_campus_memberships", _pk(),
        sa.Column("user_id", sa.String(64), nullable=False), sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False), sa.Column("created_at", TS),
        sa.UniqueConstraint("user_id", "campus_id", name="uq_membership_user_campus"))
    op.create_index("ix_disha_campus_memberships_user_id", "disha_campus_memberships", ["user_id"])
    op.create_index("ix_disha_campus_memberships_campus_id", "disha_campus_memberships", ["campus_id"])

    op.create_table(
        "disha_cases", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False), sa.Column("flag_id", sa.String(64), nullable=False),
        sa.Column("student_ref", sa.String(64), nullable=False), sa.Column("intervention_id", sa.String(64)),
        sa.Column("tier", sa.String(16)), sa.Column("reason_codes", sa.JSON, nullable=False),
        sa.Column("state", sa.String(32), nullable=False), sa.Column("owner_id", sa.String(64)),
        sa.Column("due_at", TS), sa.Column("deadline_version", sa.Integer, nullable=False),
        sa.Column("is_escalated", sa.Boolean, nullable=False), sa.Column("version", sa.Integer, nullable=False),
        sa.Column("cycle", sa.Integer, nullable=False), sa.Column("created_by", sa.String(64)),
        sa.Column("created_at", TS, nullable=False), sa.Column("updated_at", TS, nullable=False),
        sa.UniqueConstraint("campus_id", "flag_id", name="uq_cases_campus_flag"))
    op.create_index("idx_cases_queue", "disha_cases", ["campus_id", "state", "due_at"])

    op.create_table(
        "disha_case_tasks", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("disha_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False), sa.Column("generic_label", sa.String(200), nullable=False),
        sa.Column("state", sa.String(16), nullable=False), sa.Column("assignee_id", sa.String(64)),
        sa.Column("due_at", TS), sa.Column("deadline_version", sa.Integer, nullable=False),
        sa.Column("is_escalated", sa.Boolean, nullable=False), sa.Column("created_at", TS, nullable=False))
    op.create_index("idx_tasks_due", "disha_case_tasks", ["campus_id", "state", "due_at"])

    op.create_table(
        "disha_restricted_task_details", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("disha_case_tasks.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("details", sa.JSON, nullable=False), sa.Column("created_at", TS, nullable=False))

    op.create_table(
        "disha_case_events", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("disha_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(64)), sa.Column("actor_kind", sa.String(16), nullable=False),
        sa.Column("event_type", sa.String(48), nullable=False), sa.Column("from_state", sa.String(32)),
        sa.Column("to_state", sa.String(32)), sa.Column("reason_code", sa.String(64)),
        sa.Column("metadata", sa.JSON, nullable=False), sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.UniqueConstraint("campus_id", "idempotency_key", name="uq_case_events_idem"))
    op.create_index("idx_case_events_case", "disha_case_events", ["campus_id", "case_id", "created_at"])

    op.create_table(
        "disha_case_outcomes", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("disha_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cycle", sa.Integer, nullable=False), sa.Column("outcome", sa.String(16), nullable=False),
        sa.Column("intervention_id", sa.String(64), nullable=False),
        sa.Column("reason_pattern", sa.String(255), nullable=False), sa.Column("tier", sa.String(16)),
        sa.Column("checkpoint", sa.String(32)), sa.Column("recorded_by", sa.String(64)),
        sa.Column("created_at", TS, nullable=False),
        sa.UniqueConstraint("case_id", "cycle", name="uq_outcome_case_cycle"))
    op.create_index("idx_outcome_pattern", "disha_case_outcomes", ["campus_id", "intervention_id", "reason_pattern"])

    op.create_table(
        "disha_outbox", _pk(),
        sa.Column("campus_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.String(36), sa.ForeignKey("disha_cases.id", ondelete="CASCADE")),
        sa.Column("adapter_key", sa.String(32), nullable=False), sa.Column("template_key", sa.String(64), nullable=False),
        sa.Column("destination_ref", sa.String(64)), sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("status", sa.String(16), nullable=False), sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("next_attempt_at", TS, nullable=False), sa.Column("last_error", sa.String(200)),
        sa.Column("idempotency_key", sa.String(128), nullable=False), sa.Column("created_at", TS, nullable=False),
        sa.Column("sent_at", TS),
        sa.UniqueConstraint("campus_id", "idempotency_key", name="uq_outbox_idem"))
    op.create_index("idx_outbox_due", "disha_outbox", ["status", "next_attempt_at"])


def downgrade():
    for t in ("disha_outbox", "disha_case_outcomes", "disha_case_events", "disha_restricted_task_details",
              "disha_case_tasks", "disha_cases", "disha_campus_memberships"):
        op.drop_table(t)
