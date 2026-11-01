import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now
from app.modules.identity.models import User


JSONType = JSON().with_variant(JSONB(), "postgresql")


class Notification(Base):
    __tablename__ = "disha_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False)
    reference_id = Column(String(36), nullable=True)
    reference_type = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    idempotency_key = Column(String(200), nullable=True, unique=True, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], lazy="selectin")


class NotificationOutbox(Base):
    """Delivery intent written in the same transaction as the change that caused it (blueprint 07 section 5).

    The payload carries ids and template keys only; adapters render content at send time.
    """
    __tablename__ = "disha_notification_outbox"
    __table_args__ = (Index("ix_disha_notification_outbox_status_next", "status", "next_attempt_at"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    case_id = Column(String(36), nullable=True, index=True)
    recipient_id = Column(String(36), nullable=False, index=True)
    adapter_key = Column(String(50), nullable=False, default="in_app")
    template_key = Column(String(100), nullable=False)
    safe_payload = Column(JSONType, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | sent | failed | dead_letter
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_error_code = Column(String(100), nullable=True)
    idempotency_key = Column(String(250), nullable=False, unique=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class OutboxDeliveryAttempt(Base):
    """One row per delivery attempt, with the provider message id when there is one (OUT-05)."""
    __tablename__ = "disha_outbox_delivery_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    outbox_id = Column(String(36), ForeignKey("disha_notification_outbox.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False)
    adapter_key = Column(String(50), nullable=False)
    outcome = Column(String(30), nullable=False)  # sent | failed
    error_code = Column(String(100), nullable=True)
    provider_message_id = Column(String(200), nullable=True)
    attempted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
NotificationsEntity = Notification
