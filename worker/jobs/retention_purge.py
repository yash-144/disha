"""Daily retention purge (blueprint 02 worker table, 03 §13-14, 07 §6).

Retention periods per class are an OPEN product decision (blueprint 03 §14), so none is
hard-coded: each class is purged only when its period is configured, and an unset class is
left untouched. Periods (days) come from the environment:

    DISHA_RETENTION_EVIDENCE_DAYS    policy decisions + signals that no case references
    DISHA_RETENTION_RESTRICTED_DAYS  pulse reflections (ciphertext is nulled; scores stay)
    DISHA_RETENTION_TELEMETRY_DAYS   read notifications
    DISHA_RETENTION_DRY_RUN          "false" to delete; anything else (default) only reports

Never purged here: audit events (immutable), the points ledger (append-only), cases and
their events (`operational` class: no period is defined and no expiry column exists yet).
Each real purge writes one audit event per affected campus (counts only).
"""
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import delete, func, select, update

logger = logging.getLogger("disha-worker.purge")

SYSTEM_ACTOR = "system:retention_purge"
ENV_DAYS = {
    "evidence": "DISHA_RETENTION_EVIDENCE_DAYS",
    "restricted": "DISHA_RETENTION_RESTRICTED_DAYS",
    "telemetry": "DISHA_RETENTION_TELEMETRY_DAYS",
}


def _days(env_name: str) -> Optional[int]:
    raw = os.environ.get(env_name)
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        logger.error("Ignoring invalid %s=%r", env_name, raw)
        return None
    return n if n > 0 else None


def _dry_run_default() -> bool:
    return os.environ.get("DISHA_RETENTION_DRY_RUN", "true").strip().lower() != "false"


async def _by_campus(session, model, where) -> Dict[str, int]:
    res = await session.execute(select(model.campus_id, func.count()).where(*where).group_by(model.campus_id))
    return {c: n for c, n in res.all()}


async def purge_expired(session, now: datetime, periods: Dict[str, Optional[int]], dry_run: bool) -> Dict[str, Any]:
    """Run all configured purges on `session`. Returns {rule: {campus_id: rows}}; commits unless dry_run."""
    from app.modules.audit.services import AuditService
    from app.modules.cases.models import Case, Signal
    from app.modules.notifications.models import Notification
    from app.modules.policy.models import PolicyDecision
    from app.modules.wellbeing.models import PulseSubmission

    report: Dict[str, Dict[str, int]] = {}

    async def rule(name: str, model, where, apply):
        counts = await _by_campus(session, model, where)
        report[name] = counts
        if counts and not dry_run:
            await apply()

    if periods.get("evidence"):
        cutoff = now - timedelta(days=periods["evidence"])
        await rule("policy_decisions", PolicyDecision, [PolicyDecision.created_at < cutoff],
                   lambda: session.execute(delete(PolicyDecision).where(PolicyDecision.created_at < cutoff)))
        referenced = select(Case.originating_signal_id).where(Case.originating_signal_id.is_not(None))
        sig_where = [Signal.created_at < cutoff, Signal.id.not_in(referenced)]
        await rule("signals_unreferenced", Signal, sig_where,
                   lambda: session.execute(delete(Signal).where(*sig_where)))

    if periods.get("restricted"):
        cutoff = now - timedelta(days=periods["restricted"])
        where = [PulseSubmission.submitted_at < cutoff, PulseSubmission.reflection_ciphertext.is_not(None)]
        await rule("pulse_reflections", PulseSubmission, where,
                   lambda: session.execute(update(PulseSubmission).where(*where).values(reflection_ciphertext=None)))

    if periods.get("telemetry"):
        cutoff = now - timedelta(days=periods["telemetry"])
        where = [Notification.created_at < cutoff, Notification.is_read.is_(True)]
        await rule("notifications_read", Notification, where,
                   lambda: session.execute(delete(Notification).where(*where)))

    if not dry_run:
        touched: Dict[str, Dict[str, int]] = {}
        for name, counts in report.items():
            for campus, n in counts.items():
                touched.setdefault(campus, {})[name] = n
        for campus, counts in touched.items():
            await AuditService.record_event(
                session, SYSTEM_ACTOR, campus, "retention_purge", str(uuid.uuid4()), "RETENTION_PURGE", {"deleted": counts},
            )
        await session.commit()
    return report


async def run_retention_purge(session_factory=None, dry_run: Optional[bool] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    dry = _dry_run_default() if dry_run is None else dry_run
    periods = {cls: _days(env) for cls, env in ENV_DAYS.items()}
    if not any(periods.values()):
        logger.info("Retention purge: no retention period configured (%s); nothing to do.", ", ".join(ENV_DAYS.values()))
        return {}
    if session_factory is None:
        from app.core.database import AsyncSessionLocal as session_factory
    from app.shared.utils import utc_now

    logger.info("Executing data retention purge (dry_run=%s, periods=%s)...", dry, periods)
    async with session_factory() as session:
        report = await purge_expired(session, now or utc_now(), periods, dry)
    logger.info("Retention purge %s: %s", "would delete" if dry else "deleted", {k: sum(v.values()) for k, v in report.items()})
    return report
