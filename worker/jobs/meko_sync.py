"""Meko job: weekly intervention-outcome memories. (Docs are not synced to Meko.)"""
import logging
from collections import Counter

try:
    from disha_meko import MekoClient
except ImportError:  # Meko is optional
    MekoClient = None

logger = logging.getLogger("disha-worker.meko")


async def fetch_weekly_outcomes():
    """Closed interventions of the last 7 days as [{'type','outcome','tier'}] (no student data).

    TODO: query the cases/interventions tables once they exist.
    """
    return []


def summarize(outcomes: list) -> str:
    by_type = Counter((o["type"], o["outcome"]) for o in outcomes)
    lines = [f"- {t}: {out} x{n}" for (t, out), n in sorted(by_type.items())]
    return f"Weekly DISHA intervention outcomes ({len(outcomes)} closed):\n" + "\n".join(lines)


async def run_meko_weekly_outcomes():
    """Weekly: promote an aggregate outcome summary to a Meko memory."""
    client = MekoClient(component="disha-worker") if MekoClient else None
    if not client or not client.active:
        return
    outcomes = await fetch_weekly_outcomes()
    if outcomes:
        await client.remember(summarize(outcomes), tags=["interventions", "weekly-outcomes"])
