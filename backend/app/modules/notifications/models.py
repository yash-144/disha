import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now
from app.modules.identity.models import User


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


# Backwards compatibility alias for initial scaffold references
NotificationsEntity = Notification
