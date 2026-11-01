import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.shared.utils import utc_now

# Universal JSON type supporting PostgreSQL JSONB in production and SQLite JSON in tests
JSONType = JSON().with_variant(JSONB(), "postgresql")


class AuditEvent(Base):
    __tablename__ = "disha_audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String(36), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    # Column mapped to 'metadata' in the database; attribute named event_metadata to avoid collision with DeclarativeBase.metadata
    event_metadata = Column("metadata", JSONType, nullable=True)
    correlation_id = Column(String(36), nullable=True)
    prev_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
AuditEntity = AuditEvent
