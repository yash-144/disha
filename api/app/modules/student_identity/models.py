import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text

from app.core.database import Base
from app.shared.utils import utc_now


class IdentityStatus:
    ISSUED = "issued"
    MINT_PENDING = "mint_pending"
    MINTED = "minted"
    MINT_FAILED = "mint_failed"


class StudentIdentity(Base):
    """Opaque public id + private art seed for one student (blueprint 11 section 4). No PII lives here."""

    __tablename__ = "disha_student_identity"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("disha_roster.id"), nullable=False, unique=True, index=True)
    disha_id = Column(String(24), nullable=False, unique=True, index=True)  # DISHA-XXXX-XXXX-XXXX, random
    id_hash = Column(String(64), nullable=False, unique=True)  # sha256(disha_id), the contract key
    art_seed = Column(String(64), nullable=False)  # private 256-bit seed (hex); never returned by any endpoint
    wallet_address = Column(String(42), nullable=True)
    wallet_verified_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default=IdentityStatus.ISSUED, index=True)
    mint_requested_at = Column(DateTime(timezone=True), nullable=True)
    mint_tx_hash = Column(String(80), nullable=True)
    mint_submitted_at = Column(DateTime(timezone=True), nullable=True)
    mint_chain_id = Column(BigInteger, nullable=True)
    mint_block_number = Column(BigInteger, nullable=True)
    minted_at = Column(DateTime(timezone=True), nullable=True)
    mint_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class WalletChallenge(Base):
    """Single-use sign-in-with-Ethereum style challenge proving wallet ownership (NFT-01)."""

    __tablename__ = "disha_wallet_challenges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identity_id = Column(String(36), ForeignKey("disha_student_identity.id"), nullable=False, index=True)
    address = Column(String(42), nullable=False)
    nonce = Column(String(64), nullable=False)
    message = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
StudentIdentityEntity = StudentIdentity
