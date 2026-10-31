"""Glue that feeds case lifecycle events to Meko. Best effort: nothing here may fail a request.

Ids sent to Meko are hashed (student) or internal UUIDs (case, signal); never names, emails, roll numbers or marks.
"""
import json
import logging
from typing import Dict, List, Optional

from fastapi import BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.meko import fire_and_forget
from app.modules.cases.models import Case, Intervention, InterventionCatalogue, Signal

try:
    from disha_meko import playbook as pb
except ImportError:  # Meko is optional
    pb = None

log = logging.getLogger("disha.meko")
TIMEOUT_S = 10.0
OUTCOME_MAP = {"helped": "improved", "not_helped": "no_change", "mixed": "no_change"}  # "unknown" is not recorded


def reason_codes_of(evidence_snapshot: Optional[str]) -> List[str]:
    """Reason groups of the ML evidence packet (items with source ml_reason), upper-cased."""
    try:
        packet = json.loads(evidence_snapshot or "{}")
    except (TypeError, ValueError):
        return []
    codes = {str(i["metric_key"]).upper() for i in packet.get("items", []) if i.get("source") == "ml_reason" and i.get("metric_key")}
    return sorted(codes)


async def case_signal_context(db: AsyncSession, case_id: str) -> Optional[Dict]:
    """Plain facts for a policy-created case (it has originating_signal_id), else None."""
    row = (await db.execute(
        select(Case.student_id, Case.originating_signal_id, Signal.ml_tier, Signal.evidence_snapshot)
        .join(Signal, Signal.id == Case.originating_signal_id).where(Case.id == case_id))).first()
    if not row:
        return None
    return {"student_id": row[0], "signal_id": row[1], "tier": row[2], "reason_codes": reason_codes_of(row[3])}


async def _guarded(coro):
    import asyncio
    await asyncio.wait_for(coro, TIMEOUT_S)


async def schedule_case_decision(tasks: BackgroundTasks, meko, db: AsyncSession, *, case_id: str, action: str,
                                 role: str, campus_id: str, note: Optional[str] = None) -> None:
    """Queue a decision trace for accept/dismiss of a policy-created case. Call after commit."""
    try:
        if not getattr(meko, "active", False):
            return
        c = await case_signal_context(db, case_id)
        if not c:
            return
        codes = c["reason_codes"]
        fire_and_forget(tasks, _guarded(meko.trace_decision(
            decision=f"{role} chose '{action}' on an ML flag",
            rationale=(note or "") + f" Reason codes: {', '.join(codes) or 'none'}.",
            outcome=f"Action '{action}' recorded for the flag (tier {c['tier'] or 'n/a'}).",
            plan=["Show the ML flag with its reason codes.", f"Human ({role}) chooses '{action}'.",
                  "Record the decision so outcomes can inform later recalls."],
            evidence={"flag_id": c["signal_id"], "student_id": meko.hash_id(c["student_id"]), "tier": c["tier"],
                      "reason_codes": codes, "campus_id": campus_id, "case_id": case_id},
            actor=role)))
    except Exception as exc:  # noqa: BLE001
        log.warning("Meko case-decision hook failed: %s", exc)


async def schedule_case_outcome(tasks: BackgroundTasks, meko, db: AsyncSession, *, case_id: str,
                                intervention_id: str, completion_status: str, campus_id: str) -> None:
    """Queue playbook.record_outcome for a recorded intervention outcome. Call after commit."""
    try:
        outcome = OUTCOME_MAP.get(completion_status)
        if not outcome or pb is None or not getattr(meko, "active", False):
            return
        cat_id = (await db.execute(select(Intervention.catalogue_id).where(Intervention.id == intervention_id))).scalar_one_or_none()
        if not cat_id:
            return
        c = await case_signal_context(db, case_id) or {"tier": None, "reason_codes": []}
        fire_and_forget(tasks, _guarded(pb.record_outcome(
            meko, case_id=case_id, outcome=outcome, intervention_id=str(cat_id), reason_codes=c["reason_codes"],
            tier=c["tier"], checkpoint=None, campus_id=campus_id)))
    except Exception as exc:  # noqa: BLE001
        log.warning("Meko case-outcome hook failed: %s", exc)


async def catalogue_has(db: AsyncSession, campus_id: str, intervention_id: str) -> Optional[bool]:
    """Is the id an active DB catalogue entry (this campus or platform-wide)? None when no rows exist at all."""
    rows = (await db.execute(select(InterventionCatalogue.id, InterventionCatalogue.is_active).where(
        (InterventionCatalogue.campus_id == campus_id) | (InterventionCatalogue.campus_id.is_(None))))).all()
    if not rows:
        return None
    return any(r[0] == intervention_id and r[1] for r in rows)


async def playbook_text(meko, db: AsyncSession, case_id: str) -> str:
    """Playbook recall for a case's reason codes (text only). '' when Meko is off or nothing is known."""
    try:
        if not getattr(meko, "active", False):
            return ""
        c = await case_signal_context(db, case_id)
        if not c or not c["reason_codes"]:
            return ""
        q = f"Which interventions improved students with reason codes {', '.join(c['reason_codes'])}" + \
            (f" at tier {c['tier']}" if c["tier"] else "") + "?"
        import asyncio
        return ((await asyncio.wait_for(meko.recall(q, 3), TIMEOUT_S)) or "")[:800]
    except Exception as exc:  # noqa: BLE001
        log.warning("Meko playbook recall failed: %s", exc)
        return ""
