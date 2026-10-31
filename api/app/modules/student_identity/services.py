import hashlib
import logging
import re
import secrets
import uuid
from datetime import timedelta
from typing import Dict, Tuple

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import TenancyContext
from app.core.exceptions import EntityNotFoundError, StateTransitionError
from app.modules.audit.services import AuditService
from app.modules.documents import chain
from app.modules.roster.models import Student
from app.modules.student_identity.models import IdentityStatus, StudentIdentity, WalletChallenge
from app.shared.utils import utc_now

logger = logging.getLogger("disha.student_identity")

CHALLENGE_TTL = timedelta(minutes=10)
MAX_CHALLENGES_PER_HOUR = 5
MINT_RETRY_INTERVAL = timedelta(minutes=10)
SYSTEM_ACTOR = "system:identity-worker"
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_disha_id() -> str:
    parts = ["".join(secrets.choice(_ALPHABET) for _ in range(4)) for _ in range(3)]
    return "DISHA-" + "-".join(parts)


def id_hash_of(disha_id: str) -> str:
    return hashlib.sha256(disha_id.encode()).hexdigest()


def require_enabled() -> None:
    st = chain.feature_status("identity")
    if not st["enabled"]:
        msg = st.get("message") or "Student identity is not configured."
        raise HTTPException(status_code=503, detail=f"Student identity collectible is disabled: {msg}")


def _utc(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=utc_now().tzinfo)


def build_message(disha_id: str, address: str, nonce: str, issued, expires) -> str:
    return (
        f"{settings.DISHA_API_URL} wants you to sign in with your Ethereum account:\n{address}\n\n"
        f"Link this wallet to DISHA identity {disha_id}.\n\n"
        f"URI: {settings.DISHA_API_URL}\nVersion: 1\nChain ID: {settings.DISHA_BLOCKCHAIN_CHAIN_ID}\n"
        f"Nonce: {nonce}\nIssued At: {issued.isoformat()}\nExpiration Time: {expires.isoformat()}"
    )


def recover_signer(message: str, signature: str) -> str:
    try:
        from eth_account import Account  # type: ignore
        from eth_account.messages import encode_defunct  # type: ignore
    except ImportError:
        raise HTTPException(status_code=503, detail="Wallet verification is disabled: eth-account is not installed (pip install -e 'api[chain]')")
    try:
        return Account.recover_message(encode_defunct(text=message), signature=signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Signature could not be verified")


class IdentityService:
    @staticmethod
    async def _student(db: AsyncSession, tenancy: TenancyContext) -> Student:
        res = await db.execute(
            select(Student).where(Student.user_id == tenancy.user_id, Student.campus_id == tenancy.campus_id, Student.is_active == True)  # noqa: E712
        )
        student = res.scalar_one_or_none()
        if not student:  # NFT-02: only a verified student link may use this
            raise HTTPException(status_code=403, detail="No verified student record is linked to this account")
        return student

    @staticmethod
    async def get_mine(db: AsyncSession, tenancy: TenancyContext) -> StudentIdentity:
        student = await IdentityService._student(db, tenancy)
        ident = (await db.execute(select(StudentIdentity).where(StudentIdentity.student_id == student.id))).scalar_one_or_none()
        if not ident:
            raise EntityNotFoundError("StudentIdentity", "me")
        return ident

    @staticmethod
    async def issue(db: AsyncSession, tenancy: TenancyContext) -> Tuple[StudentIdentity, bool]:
        student = await IdentityService._student(db, tenancy)
        existing = (await db.execute(select(StudentIdentity).where(StudentIdentity.student_id == student.id))).scalar_one_or_none()
        if existing:
            return existing, False
        ident = StudentIdentity(
            id=str(uuid.uuid4()), campus_id=tenancy.campus_id, student_id=student.id,
            disha_id=new_disha_id(), id_hash="", art_seed=secrets.token_hex(32),
        )
        ident.id_hash = id_hash_of(ident.disha_id)
        db.add(ident)
        await db.flush()
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "student_identity", ident.id, "identity.issued", {})
        await db.commit()
        return ident, True

    @staticmethod
    async def create_challenge(db: AsyncSession, tenancy: TenancyContext, address: str) -> WalletChallenge:
        if not chain.is_address(address):
            raise HTTPException(status_code=422, detail="Invalid wallet address")
        ident = await IdentityService.get_mine(db, tenancy)
        if ident.status in (IdentityStatus.MINT_PENDING, IdentityStatus.MINTED):
            raise StateTransitionError(ident.status, "wallet_change", "the wallet is fixed once minting has been requested")
        now = utc_now()
        recent = (await db.execute(
            select(func.count()).select_from(WalletChallenge).where(
                WalletChallenge.identity_id == ident.id, WalletChallenge.created_at > now - timedelta(hours=1)
            )
        )).scalar_one()
        if recent >= MAX_CHALLENGES_PER_HOUR:
            raise HTTPException(status_code=429, detail="Too many wallet challenges; try again later")
        nonce = secrets.token_hex(16)
        expires = now + CHALLENGE_TTL
        ch = WalletChallenge(
            id=str(uuid.uuid4()), identity_id=ident.id, address=address, nonce=nonce,
            message=build_message(ident.disha_id, address, nonce, now, expires), expires_at=expires,
        )
        db.add(ch)
        await db.commit()
        return ch

    @staticmethod
    async def verify_wallet(db: AsyncSession, tenancy: TenancyContext, challenge_id: str, signature: str) -> StudentIdentity:
        ident = await IdentityService.get_mine(db, tenancy)
        ch = (await db.execute(
            select(WalletChallenge).where(WalletChallenge.id == challenge_id, WalletChallenge.identity_id == ident.id)
        )).scalar_one_or_none()
        if not ch:
            raise EntityNotFoundError("WalletChallenge", challenge_id)
        if ch.used_at is not None:
            raise HTTPException(status_code=409, detail="Challenge already used")
        if _utc(ch.expires_at) < utc_now():
            raise HTTPException(status_code=410, detail="Challenge expired")
        signer = recover_signer(ch.message, signature)
        if signer.lower() != ch.address.lower():
            raise HTTPException(status_code=403, detail="Signature does not match the claimed wallet address")
        ch.used_at = utc_now()
        ident.wallet_address = ch.address
        ident.wallet_verified_at = utc_now()
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "student_identity", ident.id, "identity.wallet_verified", {})
        await db.commit()
        return ident

    @staticmethod
    async def request_mint(db: AsyncSession, tenancy: TenancyContext) -> StudentIdentity:
        ident = await IdentityService.get_mine(db, tenancy)
        if ident.status in (IdentityStatus.MINT_PENDING, IdentityStatus.MINTED):
            raise StateTransitionError(ident.status, IdentityStatus.MINT_PENDING, "one mint per identity")
        if not ident.wallet_verified_at or not ident.wallet_address:
            raise HTTPException(status_code=409, detail="Prove wallet ownership first (POST /me/wallet/challenge then /me/wallet/verify)")
        now = utc_now()
        if ident.status == IdentityStatus.MINT_FAILED and ident.mint_requested_at and now - _utc(ident.mint_requested_at) < MINT_RETRY_INTERVAL:
            raise HTTPException(status_code=429, detail="Mint was attempted recently; retry in a few minutes")
        ident.status = IdentityStatus.MINT_PENDING
        ident.mint_requested_at = now
        ident.mint_tx_hash = None
        ident.mint_submitted_at = None
        ident.mint_error = None
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "student_identity", ident.id, "identity.mint_requested", {})
        await db.commit()
        return ident

    @staticmethod
    async def public_by_disha_id(db: AsyncSession, disha_id: str) -> StudentIdentity:
        if not re.fullmatch(r"DISHA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}", disha_id):
            raise HTTPException(status_code=404, detail="Not found")
        ident = (await db.execute(select(StudentIdentity).where(StudentIdentity.disha_id == disha_id))).scalar_one_or_none()
        if not ident:
            raise HTTPException(status_code=404, detail="Not found")
        return ident


async def _audit(db: AsyncSession, ident: StudentIdentity, action: str, meta: dict) -> None:
    await AuditService.record_event(db, SYSTEM_ACTOR, ident.campus_id, "student_identity", ident.id, action, meta)


async def process_pending_mints(db: AsyncSession, client, batch: int = 25) -> Dict[str, int]:
    """Worker side of NFT-04: submit and confirm mints. Never marks minted without a successful receipt
    (or, if someone else already minted this id for the same wallet, the on-chain owner record)."""
    stats = {"submitted": 0, "minted": 0, "failed": 0, "waiting": 0}
    rows = (await db.execute(
        select(StudentIdentity).where(StudentIdentity.status == IdentityStatus.MINT_PENDING).order_by(StudentIdentity.mint_requested_at).limit(batch)
    )).scalars().all()
    zero = chain.ZERO_ADDRESS
    for ident in rows:
        try:
            now = utc_now()
            if not ident.mint_tx_hash:
                owner = await client.identity_owner(ident.id_hash)
                if owner and owner.lower() != zero:
                    if owner.lower() == (ident.wallet_address or "").lower():
                        ident.status, ident.minted_at, ident.mint_chain_id = IdentityStatus.MINTED, now, client.chain_id
                        await _audit(db, ident, "identity.minted", {"note": "already on chain for this wallet"})
                        stats["minted"] += 1
                    else:
                        ident.status, ident.mint_error = IdentityStatus.MINT_FAILED, "identity already minted to a different address"
                        await _audit(db, ident, "identity.mint_failed", {"reason": "owner_mismatch"})
                        stats["failed"] += 1
                else:
                    tx = await client.submit_mint(ident.id_hash, ident.wallet_address)
                    ident.mint_tx_hash, ident.mint_submitted_at, ident.mint_chain_id = tx, now, client.chain_id
                    await _audit(db, ident, "identity.mint_submitted", {"tx": tx})
                    stats["submitted"] += 1
                await db.commit()
                continue
            receipt = await client.get_receipt(ident.mint_tx_hash)
            if receipt is None:
                sub = _utc(ident.mint_submitted_at)
                if sub and now - sub > timedelta(seconds=settings.DISHA_ANCHOR_CONFIRM_TIMEOUT_SECONDS):
                    ident.status, ident.mint_error = IdentityStatus.MINT_FAILED, "timeout: no receipt before the confirmation deadline"
                    await _audit(db, ident, "identity.mint_failed", {"reason": "timeout"})
                    stats["failed"] += 1
                    await db.commit()
                else:
                    stats["waiting"] += 1
                continue
            owner = await client.identity_owner(ident.id_hash) if receipt.success else None
            if receipt.success and owner and owner.lower() == (ident.wallet_address or "").lower():
                ident.status, ident.minted_at, ident.mint_block_number, ident.mint_error = IdentityStatus.MINTED, now, receipt.block_number, None
                await _audit(db, ident, "identity.minted", {"tx": ident.mint_tx_hash, "block": receipt.block_number})
                stats["minted"] += 1
            else:
                ident.status = IdentityStatus.MINT_FAILED
                ident.mint_error = "transaction reverted" if not receipt.success else "on-chain owner does not match the verified wallet"
                await _audit(db, ident, "identity.mint_failed", {"tx": ident.mint_tx_hash})
                stats["failed"] += 1
            await db.commit()
        except Exception as exc:
            logger.error("Mint step failed for identity %s: %s", ident.id, exc)
            await db.rollback()
    return stats
