import uuid
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base
from app.shared.utils import utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Campus(Base):
    __tablename__ = "disha_campuses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(300), nullable=False, default="")
    code = Column(String(50), nullable=False, unique=True, default=lambda: uuid.uuid4().hex[:16])
    is_active = Column(Boolean, nullable=False, default=True)
    # validated by app.modules.campus.schemas.CampusSettings
    settings = Column(JSONType, nullable=False, default=dict)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class MembershipInvite(Base):
    """Pending invitation by email + role + campus (NFR-TEN-04). No credentials are stored or sent: the invitee
    is linked on first Google sign-in when the verified email matches (see MembershipInviteService.claim_for_email)."""
    __tablename__ = "disha_membership_invites"
    __table_args__ = (Index("ix_disha_membership_invites_campus_email", "campus_id", "email"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    email = Column(String(320), nullable=False)  # always stored lower-cased
    role = Column(String(50), nullable=False)
    department = Column(String(200), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by = Column(String(36), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
CampusEntity = Campus
