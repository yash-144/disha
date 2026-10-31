from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint
from app.core.database import Base
from app.shared.utils import utc_now

class CampusEntity(Base):
    __tablename__ = "disha_campus"
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CampusMembership(Base):
    """Which user may act in which campus. The X-Campus-ID header is only honoured with a row here."""
    __tablename__ = "disha_campus_memberships"
    __table_args__ = (UniqueConstraint("user_id", "campus_id", name="uq_membership_user_campus"),)
    id = Column(String(36), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)  # JWT `sub`
    campus_id = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
