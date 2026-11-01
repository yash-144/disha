from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import TenancyContext, get_tenancy_context, require_role
from app.modules.documents import chain
from app.modules.student_identity.art import render_svg
from app.modules.student_identity.permissions import STUDENT_ROLES
from app.modules.student_identity.schemas import (
    IdentityResponse,
    IdentityStatusResponse,
    PublicMetadata,
    WalletChallengeRequest,
    WalletChallengeResponse,
    WalletVerifyRequest,
)
from app.modules.student_identity.services import IdentityService, require_enabled

router = APIRouter(tags=["Student identity"])


@router.get("/status", response_model=IdentityStatusResponse)
async def identity_status(tenancy: TenancyContext = Depends(get_tenancy_context)):
    """Whether the collectible is configured (any authenticated campus member)."""
    return chain.feature_status("identity")


@router.post("/me/issue", response_model=IdentityResponse)
async def issue_identity(
    response: Response,
    tenancy: TenancyContext = Depends(require_role(*STUDENT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_enabled()
    ident, created = await IdentityService.issue(db, tenancy)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return ident


@router.get("/me", response_model=IdentityResponse)
async def my_identity(
    tenancy: TenancyContext = Depends(require_role(*STUDENT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_enabled()
    return await IdentityService.get_mine(db, tenancy)


@router.post("/me/wallet/challenge", response_model=WalletChallengeResponse)
async def wallet_challenge(
    payload: WalletChallengeRequest,
    tenancy: TenancyContext = Depends(require_role(*STUDENT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_enabled()
    ch = await IdentityService.create_challenge(db, tenancy, payload.address)
    return WalletChallengeResponse(challenge_id=ch.id, message=ch.message, expires_at=ch.expires_at)


@router.post("/me/wallet/verify", response_model=IdentityResponse)
async def wallet_verify(
    payload: WalletVerifyRequest,
    tenancy: TenancyContext = Depends(require_role(*STUDENT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_enabled()
    return await IdentityService.verify_wallet(db, tenancy, payload.challenge_id, payload.signature)


@router.post("/me/mint", response_model=IdentityResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_mint(
    tenancy: TenancyContext = Depends(require_role(*STUDENT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Queue the mint (mint_pending); the worker submits and confirms it."""
    require_enabled()
    return await IdentityService.request_mint(db, tenancy)


# Public, no authentication, no PII and no link to institution records (NFT-05)
@router.get("/public/{disha_id}/metadata", response_model=PublicMetadata)
async def public_metadata(disha_id: str, db: AsyncSession = Depends(get_db)):
    require_enabled()
    ident = await IdentityService.public_by_disha_id(db, disha_id)
    return PublicMetadata(
        name=f"DISHA Student Identity {ident.disha_id}",
        description="Non-transferable DISHA student identity collectible. Contains no personal data.",
        image=f"{settings.DISHA_API_URL}/api/v1/student-identity/public/{ident.disha_id}/art.svg",
        attributes=[{"trait_type": "disha_id", "value": ident.disha_id}],
    )


@router.get("/public/{disha_id}/art.svg")
async def public_art(disha_id: str, db: AsyncSession = Depends(get_db)):
    require_enabled()
    ident = await IdentityService.public_by_disha_id(db, disha_id)
    return Response(content=render_svg(ident.art_seed), media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})
