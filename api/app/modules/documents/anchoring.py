"""Anchoring state machine driven by the worker (DOC-06). Used by worker/jobs/anchor_confirmation.py.

anchor_pending (no tx)     -> submit tx          -> anchor_pending (tx_hash set)
anchor_pending (tx_hash)   -> receipt success + on-chain record -> anchored
                           -> receipt failed / timeout          -> anchor_failed
If the hash is already on chain (first writer wins) no tx is sent and the document is anchored only after
reading the on-chain record; anchor_tx_hash stays empty to show we did not write it.
"""
import logging
from datetime import timedelta
from typing import Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.audit.services import AuditService
from app.modules.documents.chain import ChainClient
from app.modules.documents.models import Document, DocumentStatus
from app.shared.utils import utc_now

logger = logging.getLogger("disha.anchoring")

SYSTEM_ACTOR = "system:anchor-worker"


async def process_pending_anchors(db: AsyncSession, client: ChainClient, batch: int = 25) -> Dict[str, int]:
    stats = {"submitted": 0, "anchored": 0, "failed": 0, "waiting": 0}
    rows = (await db.execute(
        select(Document).where(Document.status == DocumentStatus.ANCHOR_PENDING).order_by(Document.anchor_requested_at).limit(batch)
    )).scalars().all()
    for doc in rows:
        try:
            await _step(db, client, doc, stats)
        except Exception as exc:  # keep the batch going; the doc stays pending and is retried
            logger.error("Anchor step failed for document %s: %s", doc.id, exc)
            await db.rollback()
    return stats


async def _audit(db: AsyncSession, doc: Document, action: str, meta: dict) -> None:
    await AuditService.record_event(db, SYSTEM_ACTOR, doc.campus_id, "document", doc.id, action, meta)


async def _step(db: AsyncSession, client: ChainClient, doc: Document, stats: Dict[str, int]) -> None:
    now = utc_now()
    if not doc.anchor_tx_hash:
        existing = await client.anchor_timestamp(doc.sha256)
        if existing > 0:
            doc.status = DocumentStatus.ANCHORED
            doc.anchored_at = now
            doc.anchor_chain_id = client.chain_id
            doc.anchor_error = None
            await _audit(db, doc, "document.anchored", {"sha256": doc.sha256, "tx": None, "note": "hash already on chain"})
            stats["anchored"] += 1
        else:
            tx = await client.submit_anchor(doc.sha256)
            doc.anchor_tx_hash = tx
            doc.anchor_submitted_at = now
            doc.anchor_chain_id = client.chain_id
            await _audit(db, doc, "document.anchor_submitted", {"tx": tx})
            stats["submitted"] += 1
        await db.commit()
        return

    receipt = await client.get_receipt(doc.anchor_tx_hash)
    if receipt is None:
        timeout = timedelta(seconds=settings.DISHA_ANCHOR_CONFIRM_TIMEOUT_SECONDS)
        submitted = doc.anchor_submitted_at
        if submitted is not None and submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=now.tzinfo)
        if submitted is not None and now - submitted > timeout:
            doc.status = DocumentStatus.ANCHOR_FAILED
            doc.anchor_error = "timeout: no receipt before the confirmation deadline"
            await _audit(db, doc, "document.anchor_failed", {"reason": "timeout"})
            stats["failed"] += 1
            await db.commit()
        else:
            stats["waiting"] += 1
        return

    if not receipt.success:
        doc.status = DocumentStatus.ANCHOR_FAILED
        doc.anchor_error = "transaction reverted"
        await _audit(db, doc, "document.anchor_failed", {"reason": "reverted", "tx": doc.anchor_tx_hash})
        stats["failed"] += 1
    elif await client.anchor_timestamp(doc.sha256) > 0:
        doc.status = DocumentStatus.ANCHORED
        doc.anchored_at = now
        doc.anchor_block_number = receipt.block_number
        doc.anchor_error = None
        await _audit(db, doc, "document.anchored", {"tx": doc.anchor_tx_hash, "block": receipt.block_number, "sha256": doc.sha256})
        stats["anchored"] += 1
    else:
        doc.status = DocumentStatus.ANCHOR_FAILED
        doc.anchor_error = "receipt succeeded but the hash is not in contract storage"
        await _audit(db, doc, "document.anchor_failed", {"reason": "storage_check", "tx": doc.anchor_tx_hash})
        stats["failed"] += 1
    await db.commit()
