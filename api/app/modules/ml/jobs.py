"""Worker-facing helpers (kept in the API package so they share models and services with the routes).

Scheduled scoring never guesses: a term is scored only when its `term_start` is known (from the uploaded
enrolments) and today falls inside the term. Terms without a start date are skipped and logged.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import select

from app.modules.ingestion.models import ROW_MODELS, BATCH_COMMITTED, ImportBatch
from app.modules.ml import services
from app.modules.ml.models import RUN_COMPLETED, MlScoringRun
from app.modules.ml.schemas import ScoringRunRequest

log = logging.getLogger("disha.ml.jobs")
SCHEDULER = "scheduler"


async def active_terms(db, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """[(campus, term, day since term start)] for every imported term that is currently in session."""
    today = today or date.today()
    enrol = ROW_MODELS["enrolments"]
    res = await db.execute(select(enrol.campus_id, enrol.term_id, enrol.term_start, enrol.term_length_days)
                           .join(ImportBatch, ImportBatch.id == enrol.batch_id)
                           .where(ImportBatch.status == BATCH_COMMITTED).distinct())
    seen: Dict[tuple, Dict[str, Any]] = {}
    skipped = set()
    for campus, term, start, length in res.all():
        try:
            d = (today - date.fromisoformat(str(start)[:10])).days
        except (TypeError, ValueError):
            skipped.add((campus, term))
            continue
        if 0 <= d <= (length or 0):
            seen[(campus, term)] = {"campus_id": campus, "term_id": term, "as_of_day": d}
    for k in skipped - set(seen):
        log.info("scheduled scoring skipped campus=%s term=%s: no usable term_start", *k)
    return list(seen.values())


async def run_scheduled_scoring(session_factory: Callable, today: Optional[date] = None) -> List[str]:
    """Score every in-session term once per day. Returns the ids of the runs created."""
    created: List[str] = []
    async with session_factory() as db:
        targets = await active_terms(db, today)
    for t in targets:
        async with session_factory() as db:
            done = (await db.execute(select(MlScoringRun.id).where(
                MlScoringRun.campus_id == t["campus_id"], MlScoringRun.term_id == t["term_id"],
                MlScoringRun.as_of_day == t["as_of_day"], MlScoringRun.status == RUN_COMPLETED).limit(1))).scalar_one_or_none()
            if done:
                continue
            try:
                run = await services.run_scoring(db, campus_id=t["campus_id"], triggered_by=SCHEDULER,
                                                 req=ScoringRunRequest(as_of_day=t["as_of_day"], term_id=t["term_id"]))
                run_id = run.id
                created.append(run_id)
                summary = await services.apply_policy_to_run(db, run, services.SystemActor(user_id=SCHEDULER))
                log.info("scheduled run %s policy=%s", run_id, summary)
            except services.MlError as exc:
                log.warning("scheduled scoring campus=%s term=%s not run: %s", t["campus_id"], t["term_id"], exc.message)
            except Exception:  # noqa: BLE001
                log.exception("scheduled scoring campus=%s term=%s crashed", t["campus_id"], t["term_id"])
    return created


async def drift_summaries(session_factory: Callable) -> List[Dict[str, Any]]:
    """Per campus: latest completed run's drift report against the one before it (aggregate numbers only)."""
    out: List[Dict[str, Any]] = []
    async with session_factory() as db:
        campuses = [r[0] for r in (await db.execute(select(MlScoringRun.campus_id).where(MlScoringRun.status == RUN_COMPLETED).distinct())).all()]
        for campus in campuses:
            runs = (await db.execute(select(MlScoringRun).where(MlScoringRun.campus_id == campus, MlScoringRun.status == RUN_COMPLETED)
                                     .order_by(MlScoringRun.finished_at.desc()).limit(2))).scalars().all()
            cur = runs[0]
            d = cur.data_drift or {}
            prev = (runs[1].data_drift or {}) if len(runs) > 1 else {}
            out.append({
                "campus_id": campus, "run_id": cur.id, "as_of_day": cur.as_of_day, "model_version": cur.model_version,
                "max_psi": d.get("max_psi"), "previous_max_psi": prev.get("max_psi"),
                "retrain_recommended": bool(d.get("retrain_recommended")),
                "shifted_features": [f["feature"] for f in d.get("features", []) if f.get("status") == "shift"],
                "reference_rows": d.get("reference_rows"), "current_rows": d.get("current_rows"),
            })
    return out
