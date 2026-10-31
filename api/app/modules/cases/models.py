"""Case lifecycle tables: cases, tasks, restricted details, append-only events, outcomes, outbox."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.utils import utc_now


def _id() -> str:
    return str(uuid.uuid4())


class Case(Base):
    __tablename__ = "disha_cases"
    __table_args__ = (
        UniqueConstraint("campus_id", "flag_id", name="uq_cases_campus_flag"),
        Index("idx_cases_queue", "campus_id", "state", "due_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    flag_id: Mapped[str] = mapped_column(String(64))  # the ML flag this case answers (idempotent create)
    student_ref: Mapped[str] = mapped_column(String(64))  # campus-side student id; never sent to Meko unhashed
    intervention_id: Mapped[Optional[str]] = mapped_column(String(64))
    tier: Mapped[Optional[str]] = mapped_column(String(16))
    reason_codes: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(32), default="action_planned")
    owner_id: Mapped[Optional[str]] = mapped_column(String(64))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_version: Mapped[int] = mapped_column(Integer, default=1)  # bumped when due_at changes
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)  # optimistic lock (CASE-SM-04)
    cycle: Mapped[int] = mapped_column(Integer, default=1)  # reopen starts a new outcome cycle
    created_by: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CaseTask(Base):
    __tablename__ = "disha_case_tasks"
    __table_args__ = (Index("idx_tasks_due", "campus_id", "state", "due_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    case_id: Mapped[str] = mapped_column(ForeignKey("disha_cases.id", ondelete="CASCADE"))
    domain: Mapped[str] = mapped_column(String(32))
    generic_label: Mapped[str] = mapped_column(String(200))  # restricted context lives in RestrictedTaskDetail
    state: Mapped[str] = mapped_column(String(16), default="pending")
    assignee_id: Mapped[Optional[str]] = mapped_column(String(64))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_version: Mapped[int] = mapped_column(Integer, default=1)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RestrictedTaskDetail(Base):
    __tablename__ = "disha_restricted_task_details"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    task_id: Mapped[str] = mapped_column(ForeignKey("disha_case_tasks.id", ondelete="CASCADE"), unique=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CaseEvent(Base):
    """Append-only audit trail: updates and deletes are refused (see listeners below)."""
    __tablename__ = "disha_case_events"
    __table_args__ = (
        UniqueConstraint("campus_id", "idempotency_key", name="uq_case_events_idem"),
        Index("idx_case_events_case", "campus_id", "case_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    case_id: Mapped[str] = mapped_column(ForeignKey("disha_cases.id", ondelete="CASCADE"))
    actor_id: Mapped[Optional[str]] = mapped_column(String(64))
    actor_kind: Mapped[str] = mapped_column(String(16), default="user")  # user | system_worker
    event_type: Mapped[str] = mapped_column(String(48))
    from_state: Mapped[Optional[str]] = mapped_column(String(32))
    to_state: Mapped[Optional[str]] = mapped_column(String(32))
    reason_code: Mapped[Optional[str]] = mapped_column(String(64))
    event_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), default=_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


@event.listens_for(CaseEvent, "before_update")
@event.listens_for(CaseEvent, "before_delete")
def _events_are_append_only(*_):
    raise ValueError("case_events is append-only")


class CaseOutcome(Base):
    """One outcome per case cycle. reason_pattern is the sorted reason codes joined with '+'."""
    __tablename__ = "disha_case_outcomes"
    __table_args__ = (
        UniqueConstraint("case_id", "cycle", name="uq_outcome_case_cycle"),
        Index("idx_outcome_pattern", "campus_id", "intervention_id", "reason_pattern"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    case_id: Mapped[str] = mapped_column(ForeignKey("disha_cases.id", ondelete="CASCADE"))
    cycle: Mapped[int] = mapped_column(Integer, default=1)
    outcome: Mapped[str] = mapped_column(String(16))  # improved | no_change | worse
    intervention_id: Mapped[str] = mapped_column(String(64))
    reason_pattern: Mapped[str] = mapped_column(String(255), default="")
    tier: Mapped[Optional[str]] = mapped_column(String(16))
    checkpoint: Mapped[Optional[str]] = mapped_column(String(32))
    recorded_by: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class OutboxItem(Base):
    """Transactional outbox: written in the same commit as the case change it announces."""
    __tablename__ = "disha_outbox"
    __table_args__ = (
        UniqueConstraint("campus_id", "idempotency_key", name="uq_outbox_idem"),
        Index("idx_outbox_due", "status", "next_attempt_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    campus_id: Mapped[str] = mapped_column(String(64))
    case_id: Mapped[Optional[str]] = mapped_column(ForeignKey("disha_cases.id", ondelete="CASCADE"))
    adapter_key: Mapped[str] = mapped_column(String(32), default="in_app")
    template_key: Mapped[str] = mapped_column(String(64))
    destination_ref: Mapped[Optional[str]] = mapped_column(String(64))
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # IDs and template keys only (OUT-04)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | sent | dead_letter
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_error: Mapped[Optional[str]] = mapped_column(String(200))
    idempotency_key: Mapped[str] = mapped_column(String(128), default=_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
