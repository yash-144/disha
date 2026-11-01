import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.shared.utils import utc_now


class User(Base):
    __tablename__ = "disha_identity"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False, unique=True, index=True)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(300), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    memberships = relationship("Membership", back_populates="user", lazy="selectin")


class Membership(Base):
    __tablename__ = "disha_memberships"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    campus_id = Column(String(36), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    department = Column(String(200), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="memberships")


# Backwards compatibility alias for initial scaffold references
IdentityEntity = User
