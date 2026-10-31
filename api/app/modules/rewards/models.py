import uuid
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event,
)
from app.core.database import Base
from app.shared.utils import utc_now


class LedgerEntry(Base):
    """Append-only points ledger (PTS-01). Balance = SUM(points). Corrections are new rows."""
    __tablename__ = "disha_reward_ledger"
    __table_args__ = (UniqueConstraint("campus_id", "idempotency_key", name="uq_reward_ledger_idem"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    entry_type = Column(String(20), nullable=False)  # award | redemption | reversal
    activity_key = Column(String(60), nullable=True)
    source_ref = Column(String(200), nullable=True)
    points = Column(Integer, nullable=False)  # + for award/reversal, - for redemption
    idempotency_key = Column(String(300), nullable=False)
    reference_id = Column(String(36), nullable=True)  # redemption id
    created_by = Column(String(36), nullable=True)  # null = system
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class AppendOnlyError(RuntimeError):
    pass


@event.listens_for(LedgerEntry, "before_update")
def _ledger_no_update(mapper, connection, target):
    raise AppendOnlyError("reward ledger entries are append-only")


@event.listens_for(LedgerEntry, "before_delete")
def _ledger_no_delete(mapper, connection, target):
    raise AppendOnlyError("reward ledger entries are append-only")


class RewardItem(Base):
    __tablename__ = "disha_reward_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    cost_points = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Redemption(Base):
    __tablename__ = "disha_reward_redemptions"
    __table_args__ = (UniqueConstraint("campus_id", "student_id", "idempotency_key", name="uq_redemption_idem"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("disha_reward_items.id"), nullable=False, index=True)
    cost_points = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="requested", index=True)  # requested|approved|fulfilled|rejected
    idempotency_key = Column(String(300), nullable=False)
    handled_by = Column(String(36), nullable=True)
    handled_at = Column(DateTime(timezone=True), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
RewardsEntity = LedgerEntry
