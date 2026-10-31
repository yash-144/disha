"""Submit and confirm on-chain document anchors and student identity mints (blueprint 11, DOC-06, NFT-04).

Does nothing, loudly, when the chain is not configured: documents stay as they are and no anchor is recorded.
"""
import logging

logger = logging.getLogger("disha-worker.anchor")

_warned_disabled = False


async def run_anchor_confirmation() -> dict:
    global _warned_disabled
    try:
        from app.core.database import AsyncSessionLocal
        from app.modules.documents import chain
        from app.modules.documents.anchoring import process_pending_anchors
        from app.modules.student_identity.services import process_pending_mints
    except ImportError as exc:  # worker started without api/app on PYTHONPATH
        logger.error("Anchor job cannot import the API package (%s); nothing was anchored.", exc)
        return {"status": "import_error"}

    stats = {}
    for feature, step in (("anchoring", process_pending_anchors), ("identity", process_pending_mints)):
        client = chain.get_chain_client(feature)
        if client is None:
            status = chain.feature_status(feature)
            if not _warned_disabled:
                logger.warning(
                    "Chain %s is NOT CONFIGURED (%s). Pending items stay pending and nothing is recorded as on-chain.",
                    feature, status.get("message") or ", ".join(status.get("missing", [])),
                )
            stats[feature] = "not_configured"
            continue
        async with AsyncSessionLocal() as db:
            stats[feature] = await step(db, client)
    _warned_disabled = True
    if any(isinstance(v, dict) and any(v.values()) for v in stats.values()):
        logger.info("Anchor job: %s", stats)
    return stats
