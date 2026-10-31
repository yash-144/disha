from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disha_id: str
    status: str
    wallet_address: Optional[str] = None
    wallet_verified_at: Optional[datetime] = None
    mint_tx_hash: Optional[str] = None
    mint_block_number: Optional[int] = None
    minted_at: Optional[datetime] = None
    mint_error: Optional[str] = None
    created_at: datetime


class IdentityStatusResponse(BaseModel):
    enabled: bool
    missing: List[str] = []
    message: Optional[str] = None
    chain_id: Optional[int] = None


class WalletChallengeRequest(BaseModel):
    address: str = Field(..., min_length=42, max_length=42)


class WalletChallengeResponse(BaseModel):
    challenge_id: str
    message: str
    expires_at: datetime


class WalletVerifyRequest(BaseModel):
    challenge_id: str
    signature: str = Field(..., min_length=10, max_length=300)


class PublicMetadata(BaseModel):
    name: str
    description: str
    image: str
    attributes: List[Dict[str, Any]]
