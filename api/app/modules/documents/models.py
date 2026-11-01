import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base
from app.shared.utils import utc_now


class DocumentStatus:
    DRAFT = "draft"
    FINALIZED = "finalized"
    ANCHOR_PENDING = "anchor_pending"
    ANCHORED = "anchored"
    ANCHOR_FAILED = "anchor_failed"
    VERIFICATION_MISMATCH = "verification_mismatch"

    ALL = (DRAFT, FINALIZED, ANCHOR_PENDING, ANCHORED, ANCHOR_FAILED, VERIFICATION_MISMATCH)


class Document(Base):
    """A stored file with a frozen SHA-256 (blueprint 11). Never holds personal data in `document_ref`."""

    __tablename__ = "disha_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    # Opaque reference (DOC-<uuid>); this is the only identifier that may leave the institution.
    document_ref = Column(String(64), nullable=False, unique=True, index=True)
    case_id = Column(String(36), ForeignKey("disha_cases.id"), nullable=True, index=True)
    kind = Column(String(50), nullable=False, default="other")
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False)
    storage_backend = Column(String(20), nullable=False)
    storage_key = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default=DocumentStatus.DRAFT, index=True)
    version = Column(Integer, nullable=False, default=1)
    previous_version_id = Column(String(36), ForeignKey("disha_documents.id"), nullable=True)
    uploaded_by = Column(String(36), ForeignKey("disha_identity.id"), nullable=False, index=True)
    finalized_by = Column(String(36), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    # Anchoring (only ever filled from a confirmed chain receipt)
    anchor_requested_by = Column(String(36), nullable=True)
    anchor_requested_at = Column(DateTime(timezone=True), nullable=True)
    anchor_tx_hash = Column(String(80), nullable=True)
    anchor_submitted_at = Column(DateTime(timezone=True), nullable=True)
    anchor_chain_id = Column(Integer, nullable=True)
    anchor_block_number = Column(BigInteger, nullable=True)
    anchored_at = Column(DateTime(timezone=True), nullable=True)
    anchor_error = Column(Text, nullable=True)

    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_verification_ok = Column(String(5), nullable=True)  # "true" / "false"

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


# Backwards compatibility alias for initial scaffold references
DocumentsEntity = Document
