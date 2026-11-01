from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_ref: str
    campus_id: str
    case_id: Optional[str] = None
    kind: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    status: str
    version: int
    previous_version_id: Optional[str] = None
    uploaded_by: str
    finalized_at: Optional[datetime] = None
    anchor_tx_hash: Optional[str] = None
    anchor_chain_id: Optional[int] = None
    anchor_block_number: Optional[int] = None
    anchored_at: Optional[datetime] = None
    anchor_error: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    last_verification_ok: Optional[str] = None
    created_at: datetime


class VerificationCheck(BaseModel):
    name: str
    ran: bool
    ok: Optional[bool] = None
    detail: str = ""


class VerificationResponse(BaseModel):
    document_id: str
    document_ref: str
    status: str
    ok: bool
    checks: List[VerificationCheck]
    verified_at: datetime


class AnchoringStatusResponse(BaseModel):
    enabled: bool
    missing: List[str] = []
    message: Optional[str] = None
    chain_id: Optional[int] = None


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in_seconds: Optional[int] = None
    kind: str  # "signed" (object store, short-lived) or "api" (authenticated API route)
