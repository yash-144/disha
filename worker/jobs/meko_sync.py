"""Meko job: weekly intervention-outcome memories. (Docs are not synced to Meko.)"""
import logging
from collections import Counter

try:
    from disha_meko import MekoClient
except ImportError:  # Meko is optional
    MekoClient = None

logger = logging.getLogger("disha-worker.meko")


async def fetch_weekly_outcomes(factory=None):
    """Intervention outcomes recorded in the last 7 days as [{'type','outcome','tier'}] (no student data)."""
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from ._db import session_factory

    from app.modules.cases.models import Case, Intervention, InterventionCatalogue, InterventionOutcome, Signal

    since = datetime.now(timezone.utc) - timedelta(days=7)
    async with (factory or session_factory())() as db:
        rows = (await db.execute(
            select(InterventionCatalogue.name, InterventionOutcome.completion_status, Signal.ml_tier)
            .select_from(InterventionOutcome)
            .join(Intervention, Intervention.id == InterventionOutcome.intervention_id)
            .join(InterventionCatalogue, InterventionCatalogue.id == Intervention.catalogue_id)
            .join(Case, Case.id == InterventionOutcome.case_id)
            .outerjoin(Signal, Signal.id == Case.originating_signal_id)
            .where(InterventionOutcome.completed_at >= since)
        )).all()
    return [{"type": r[0], "outcome": r[1], "tier": r[2] or "n/a"} for r in rows]


def summarize(outcomes: list) -> str:
    by_type = Counter((o["type"], o["outcome"]) for o in outcomes)
    lines = [f"- {t}: {out} x{n}" for (t, out), n in sorted(by_type.items())]
    return f"Weekly DISHA intervention outcomes ({len(outcomes)} closed):\n" + "\n".join(lines)


async def run_meko_weekly_outcomes():
    """Weekly: promote an aggregate outcome summary to a Meko memory."""
    client = MekoClient(component="disha-worker") if MekoClient else None
    if not client or not client.active:
        return
    try:
        outcomes = await fetch_weekly_outcomes()
        if outcomes:
            await client.remember(summarize(outcomes), tags=["interventions", "weekly-outcomes"])
    except Exception as exc:  # noqa: BLE001 - Meko/DB trouble must not fail the scheduler
        logger.warning("Meko weekly outcomes failed: %s", exc)
