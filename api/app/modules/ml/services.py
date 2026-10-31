"""Rolling-risk-model pipeline: model registry, scoring service, queries, and the policy handoff.

Real data only. Tables come from the campus's committed import batches (ingestion module) and the model
bundle from DISHA_ML_BUNDLE_PATH. If either is missing the caller gets a 409 with a machine code; nothing is
generated, defaulted or simulated. `disha_ml.synthetic` is never imported here.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import DishaBaseException
from app.modules.audit.services import AuditService
from app.modules.ingestion.models import ROW_MODELS, ImportBatch
from app.modules.ingestion.services import active_batch_ids
from app.modules.ml.models import RUN_COMPLETED, RUN_FAILED, RUN_RUNNING, MlRiskScore, MlScoringRun
from app.modules.ml.schemas import RiskFlag, ScoringRunRequest
from app.shared.utils import utc_now

log = logging.getLogger("disha.ml")

TIER_FLAG = {"HIGH": "high", "MEDIUM": "medium", "WATCH": "watch", "ON_TRACK": "none"}
RUN_STALE_AFTER = timedelta(minutes=30)
INSERT_CHUNK = 400


class MlError(DishaBaseException):
    def __init__(self, message: str, status_code: int, code: str, details: Optional[dict] = None):
        super().__init__(message, status_code, {"code": code, **(details or {})})


# ---- pseudonyms ---------------------------------------------------------------------------
def hash_student_ref(ref: str) -> str:
    """Stable pseudonym for a campus student id (same formula as disha_meko.redact.hash_id when MEKO_PII_SALT is the salt)."""
    salt = settings.DISHA_STUDENT_REF_SALT or os.getenv("MEKO_PII_SALT", "") or settings.DISHA_JWT_SECRET
    return "s_" + hmac.new(salt.encode(), str(ref).encode(), hashlib.sha256).hexdigest()[:12]


# ---- model registry -----------------------------------------------------------------------
@dataclass
class LoadedModel:
    bundle: Dict[str, Any]
    manifest: Dict[str, Any]
    sha256: str
    version: str
    path: str


_registry: Dict[str, Tuple[float, LoadedModel]] = {}


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model_sync(path: Optional[str] = None) -> LoadedModel:
    """Load and check the bundle folder (model.joblib + manifest.json). Cached until the files change."""
    root = Path(path or settings.DISHA_ML_BUNDLE_PATH)
    mf, mj = root / "manifest.json", root / "model.joblib"
    if not mf.is_file() or not mj.is_file():
        raise MlError(f"No model bundle at {root} (needs model.joblib and manifest.json). Train one with "
                      "`python -m disha_ml.rolling.train` or set DISHA_ML_BUNDLE_PATH.", 409, "MODEL_UNAVAILABLE")
    stamp = max(mf.stat().st_mtime, mj.stat().st_mtime)
    hit = _registry.get(str(root))
    if hit and hit[0] == stamp:
        return hit[1]
    try:
        manifest = json.loads(mf.read_text())
        from disha_ml.rolling.score import load_bundle
        bundle = load_bundle(root)
    except Exception as exc:  # noqa: BLE001
        raise MlError(f"Model bundle at {root} could not be loaded: {exc}", 409, "MODEL_UNAVAILABLE") from exc
    if list(manifest.get("features", [])) != list(bundle.get("features", [])):
        raise MlError("manifest.json features do not match model.joblib; refusing to score", 409, "MODEL_MANIFEST_MISMATCH")
    if manifest.get("bundle_version") != bundle.get("version"):
        raise MlError("manifest.json bundle_version does not match model.joblib; refusing to score", 409, "MODEL_MANIFEST_MISMATCH")
    sha = _sha256_file(mj)
    loaded = LoadedModel(bundle, manifest, sha, f"{manifest.get('model', 'rolling')}/v{manifest.get('bundle_version')}+{sha[:8]}", str(root))
    _registry[str(root)] = (stamp, loaded)
    return loaded


async def get_model() -> LoadedModel:
    return await asyncio.to_thread(load_model_sync)


def model_info(m: LoadedModel) -> Dict[str, Any]:
    res = (m.manifest.get("results") or {}).get("test") or {}
    cut = m.manifest.get("cutoffs") or m.bundle.get("cutoffs") or {}
    return {
        "model": m.manifest.get("model", "rolling"), "bundle_version": m.manifest.get("bundle_version"),
        "model_version": m.version, "bundle_sha256": m.sha256,
        "trained_terms": [str(t) for t in m.bundle.get("trained_terms", [])],
        "features": list(m.bundle.get("features", [])),
        "cutoffs": {k: (v or {}).get("threshold") for k, v in (m.bundle.get("cutoffs") or {}).items()},
        "capacity_share": m.bundle.get("capacity_share"), "dataset": m.manifest.get("dataset"),
        "headline_metrics": {
            **{k: res[k] for k in ("roc_auc", "pr_auc", "brier", "ece") if k in res},
            "alert_precision_at_cutoff": {k: (v or {}).get("precision") for k, v in cut.items()},
        },
        "notes": ["Probabilities are calibrated risks of Fail or Withdrawn; they are evidence for humans, not decisions.",
                  "Alert precision is the share of flagged students who ended at risk; it is not accuracy."],
    }


# ---- building canonical tables from the database ------------------------------------------------
_COLS = {
    "students": ["student_ref", "program_level", "year_of_study", "tenth_pct", "twelfth_pct", "entrance_pct",
                 "prior_education_ord", "gender", "region", "imd_band", "disability", "age_band"],
    "enrolments": ["student_ref", "term_id", "course_id", "term_length_days", "term_start", "outcome",
                   "prev_attempts", "credit_load", "section"],
    "assessments": ["assessment_id", "course_id", "term_id", "due_day", "weight", "type"],
    "results": ["student_ref", "assessment_id", "submitted_day", "score_pct"],
    "activity": ["student_ref", "course_id", "term_id", "day", "count"],
    "withdrawals": ["student_ref", "course_id", "term_id", "day"],
}


async def _frame(db: AsyncSession, name: str, campus_id: str, batch_ids: List[str]) -> pd.DataFrame:
    model = ROW_MODELS[name]
    cols = _COLS[name]
    order = [model.batch_id, model.id]
    res = await db.execute(select(*[getattr(model, c) for c in cols]).where(
        model.campus_id == campus_id, model.batch_id.in_(batch_ids)).order_by(*order))
    df = pd.DataFrame(res.all(), columns=cols)
    return df.rename(columns={"student_ref": "student_id"})


async def build_tables(db: AsyncSession, campus_id: str, term_id: Optional[str] = None
                       ) -> Tuple[Dict[str, pd.DataFrame], List[str], Dict[str, Optional[str]]]:
    """Canonical tables for a campus from its active batches. Returns (tables, batch_ids, student_ref -> roster id)."""
    batch_ids = await active_batch_ids(db, campus_id)
    if not batch_ids:
        raise MlError("This campus has no ingested data. Import the canonical tables first (POST /api/v1/ingestion/imports).",
                      409, "NO_INGESTED_DATA")
    t = {n: await _frame(db, n, campus_id, batch_ids) for n in _COLS}
    t["students"] = t["students"].drop_duplicates("student_id", keep="last")   # later batch wins
    if term_id is not None:
        t["enrolments"] = t["enrolments"][t["enrolments"]["term_id"] == term_id]
        if t["enrolments"].empty:
            raise MlError(f"No ingested enrolments for term '{term_id}'", 409, "NO_INGESTED_DATA", {"term_id": term_id})
        t["assessments"] = t["assessments"][t["assessments"]["term_id"] == term_id]
        t["results"] = t["results"][t["results"]["assessment_id"].isin(set(t["assessments"]["assessment_id"]))]
        t["activity"] = t["activity"][t["activity"]["term_id"] == term_id]
        t["withdrawals"] = t["withdrawals"][t["withdrawals"]["term_id"] == term_id]
    if t["enrolments"].empty or t["assessments"].empty:
        raise MlError("Ingested data has no enrolments or no assessments to score", 409, "NO_INGESTED_DATA")
    links = await _roster_ids(db, campus_id, batch_ids)
    return t, batch_ids, links


async def _roster_ids(db: AsyncSession, campus_id: str, batch_ids: List[str]) -> Dict[str, Optional[str]]:
    m = ROW_MODELS["enrolments"]
    res = await db.execute(select(m.student_ref, m.roster_student_id).where(m.campus_id == campus_id, m.batch_id.in_(batch_ids)))
    out: Dict[str, Optional[str]] = {}
    for ref, rid in res.all():
        out[ref] = rid or out.get(ref)
    return out


def resolve_as_of(tables: Dict[str, pd.DataFrame], req: ScoringRunRequest) -> int:
    if req.as_of_day is not None:
        return int(req.as_of_day)
    if req.as_of_date is None:
        raise MlError("Give as_of_day, or as_of_date together with term_id", 422, "AS_OF_REQUIRED")
    starts = pd.to_datetime(tables["enrolments"]["term_start"], errors="coerce").dropna().dt.normalize().unique()
    if len(starts) != 1:
        raise MlError("as_of_date needs exactly one term with a known term_start; pass term_id", 422, "AS_OF_AMBIGUOUS")
    day = (pd.Timestamp(req.as_of_date) - pd.Timestamp(starts[0])).days
    if day < 0:
        raise MlError("as_of_date is before the term starts", 422, "AS_OF_BEFORE_TERM_START")
    return int(day)


def _as_of_date(starts: Dict[Tuple[str, str], pd.Timestamp], course: str, term: str, day: int) -> Optional[str]:
    s = starts.get((course, term))
    return None if s is None else (s + pd.Timedelta(days=day)).date().isoformat()


# ---- scoring run ------------------------------------------------------------------------------------
async def run_scoring(db: AsyncSession, *, campus_id: str, triggered_by: str, req: ScoringRunRequest) -> MlScoringRun:
    if not campus_id or campus_id == "platform-global":
        raise MlError("Select a campus (X-Campus-ID) before scoring", 400, "CAMPUS_REQUIRED")
    model = await get_model()
    tables, batch_ids, links = await build_tables(db, campus_id, req.term_id)
    as_of = resolve_as_of(tables, req)

    busy = (await db.execute(select(MlScoringRun.id).where(
        MlScoringRun.campus_id == campus_id, MlScoringRun.status == RUN_RUNNING,
        MlScoringRun.started_at > utc_now() - RUN_STALE_AFTER).limit(1))).scalar_one_or_none()
    if busy:
        raise MlError("A scoring run is already in progress for this campus", 409, "RUN_IN_PROGRESS", {"run_id": busy})

    run = MlScoringRun(campus_id=campus_id, triggered_by=triggered_by, status=RUN_RUNNING, term_id=req.term_id,
                       as_of_day=as_of, model_version=model.version, bundle_sha256=model.sha256,
                       batch_ids=batch_ids, tier_counts={}, n_scored=0, started_at=utc_now())
    db.add(run)
    await db.commit()

    try:
        from disha_ml.rolling.score import score_snapshot
        payload = await asyncio.to_thread(score_snapshot, tables, as_of, model.bundle)
        data = payload.to_dict()
        starts = _term_starts(tables["enrolments"])
        rows = []
        for s in data["students"]:
            ref = str(s["student_id"])
            risk = s["risk"]
            rows.append({
                "run_id": run.id, "campus_id": campus_id, "student_ref": ref,
                "external_student_ref_hash": hash_student_ref(ref), "student_id": links.get(ref),
                "course_id": s["course_id"], "term_id": s["term_id"], "as_of_day": int(s["as_of_day"]),
                "as_of_date": _as_of_date(starts, s["course_id"], s["term_id"], int(s["as_of_day"])),
                "probability": float(risk["probability"]), "tier": risk["tier"], "signal": bool(risk["signal"]),
                "previous_probability": risk.get("previous_probability"), "previous_tier": risk.get("previous_tier"),
                "direction": risk.get("direction"), "reasons": s["reasons"], "insight": s,
                "model_version": model.version, "created_at": utc_now(),
            })
        for i in range(0, len(rows), INSERT_CHUNK):
            chunk = rows[i:i + INSERT_CHUNK]
            for r in chunk:
                r["id"] = _uuid()
            await db.execute(MlRiskScore.__table__.insert(), chunk)
        counts: Dict[str, int] = {}
        for r in rows:
            counts[r["tier"]] = counts.get(r["tier"], 0) + 1
        run.status, run.n_scored, run.tier_counts = RUN_COMPLETED, len(rows), counts
        run.schema_version = data.get("schema_version")
        run.cohorts, run.data_drift, run.model_info = data["cohorts"], data["data_drift"], data["model"]
        run.finished_at = utc_now()
        await AuditService.record_event(
            db, actor_id=triggered_by, campus_id=campus_id, entity_type="ml_scoring_run", entity_id=run.id,
            action="ml.scoring_run.completed",
            event_metadata={"as_of_day": as_of, "term_id": req.term_id, "n_scored": len(rows), "tier_counts": counts,
                            "model_version": model.version, "batch_ids": batch_ids})
        await db.commit()
    except Exception as exc:  # noqa: BLE001 - recorded on the run, then surfaced
        await db.rollback()
        log.exception("scoring run %s failed", run.id)
        failed = (await db.execute(select(MlScoringRun).where(MlScoringRun.id == run.id))).scalar_one()
        failed.status, failed.error, failed.finished_at = RUN_FAILED, str(exc)[:2000], utc_now()
        await AuditService.record_event(db, actor_id=triggered_by, campus_id=campus_id, entity_type="ml_scoring_run",
                                        entity_id=run.id, action="ml.scoring_run.failed", event_metadata={"error": str(exc)[:300]})
        await db.commit()
        raise MlError(f"Scoring failed: {exc}", 422, "SCORING_FAILED", {"run_id": run.id}) from exc

    await _meko_after_run(data)
    return run


def _uuid() -> str:
    import uuid
    return str(uuid.uuid4())


def _term_starts(enrol: pd.DataFrame) -> Dict[Tuple[str, str], pd.Timestamp]:
    out: Dict[Tuple[str, str], pd.Timestamp] = {}
    for (c, t), g in enrol.groupby(["course_id", "term_id"]):
        d = pd.to_datetime(g["term_start"], errors="coerce").dropna()
        if len(d):
            out[(c, t)] = d.iloc[0].normalize()
    return out


async def _meko_after_run(payload: Dict[str, Any]) -> None:
    """Academic-journey memories (tier changes, drift events). Ids are hashed inside the Meko client; failures are ignored."""
    if not settings.DISHA_ML_MEKO_HOOKS:
        return
    try:
        from disha_ml import meko_hooks
        await asyncio.wait_for(asyncio.to_thread(meko_hooks.record_assessment_updates, payload), timeout=20)
    except Exception as exc:  # noqa: BLE001 - Meko is optional and must never fail a run
        log.warning("Meko journey hook skipped: %s", exc)


# ---- queries ---------------------------------------------------------------------------------------------
async def latest_run(db: AsyncSession, campus_id: str, term_id: Optional[str] = None) -> MlScoringRun:
    q = select(MlScoringRun).where(MlScoringRun.campus_id == campus_id, MlScoringRun.status == RUN_COMPLETED)
    if term_id:
        q = q.where(or_(MlScoringRun.term_id == term_id, MlScoringRun.term_id.is_(None)))
    run = (await db.execute(q.order_by(MlScoringRun.finished_at.desc()).limit(1))).scalar_one_or_none()
    if not run:
        raise MlError("No completed scoring run for this campus yet. Trigger one with POST /api/v1/ml/runs.", 404, "NO_SCORING_RUN")
    return run


async def get_run(db: AsyncSession, campus_id: str, run_id: str) -> MlScoringRun:
    run = (await db.execute(select(MlScoringRun).where(MlScoringRun.id == run_id, MlScoringRun.campus_id == campus_id))).scalar_one_or_none()
    if not run:
        raise MlError("Scoring run not found in the active campus", 404, "RUN_NOT_FOUND")
    return run


async def list_runs(db: AsyncSession, campus_id: str, page: int, page_size: int) -> Tuple[List[MlScoringRun], int]:
    total = (await db.execute(select(func.count()).select_from(MlScoringRun).where(MlScoringRun.campus_id == campus_id))).scalar_one()
    rows = (await db.execute(select(MlScoringRun).where(MlScoringRun.campus_id == campus_id)
                             .order_by(MlScoringRun.started_at.desc()).limit(page_size).offset((page - 1) * page_size))).scalars().all()
    return list(rows), int(total)


async def list_scores(db: AsyncSession, campus_id: str, *, run: MlScoringRun, tier: Optional[str], course_id: Optional[str],
                      term_id: Optional[str], signal_only: bool, page: int, page_size: int) -> Tuple[List[MlRiskScore], int]:
    q = select(MlRiskScore).where(MlRiskScore.run_id == run.id, MlRiskScore.campus_id == campus_id)
    if tier:
        q = q.where(MlRiskScore.tier == tier.upper())
    if course_id:
        q = q.where(MlRiskScore.course_id == course_id)
    if term_id:
        q = q.where(MlRiskScore.term_id == term_id)
    if signal_only:
        q = q.where(MlRiskScore.signal.is_(True))
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.order_by(MlRiskScore.probability.desc(), MlRiskScore.id)
                             .limit(page_size).offset((page - 1) * page_size))).scalars().all()
    return list(rows), int(total)


async def student_scores(db: AsyncSession, campus_id: str, key: str, course_id: Optional[str] = None
                         ) -> List[MlRiskScore]:
    """Latest score per (course, term) for a student addressed by roster id or pseudonym hash."""
    q = (select(MlRiskScore).join(MlScoringRun, MlScoringRun.id == MlRiskScore.run_id)
         .where(MlRiskScore.campus_id == campus_id, MlScoringRun.status == RUN_COMPLETED,
                or_(MlRiskScore.student_id == key, MlRiskScore.external_student_ref_hash == key)))
    if course_id:
        q = q.where(MlRiskScore.course_id == course_id)
    rows = (await db.execute(q.order_by(MlScoringRun.finished_at.desc(), MlRiskScore.as_of_day.desc()))).scalars().all()
    seen, out = set(), []
    for r in rows:
        k = (r.course_id, r.term_id)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


# ---- policy handoff ------------------------------------------------------------------------------------------
async def flags_for_run(session: AsyncSession, run_id: str) -> List[RiskFlag]:
    """Every scored enrolment of a run as a RiskFlag (tier 'none' = on track; filter on tier as needed)."""
    res = await session.execute(select(MlRiskScore).where(MlRiskScore.run_id == run_id)
                                .order_by(MlRiskScore.probability.desc(), MlRiskScore.id))
    return [RiskFlag(
        campus_id=s.campus_id, student_id=s.student_id, external_student_ref_hash=s.external_student_ref_hash,
        course_ref=f"{s.course_id}:{s.term_id}", as_of=s.as_of_date or f"day:{s.as_of_day}",
        tier=TIER_FLAG.get(s.tier, "none"), probability=float(s.probability), reasons=list(s.reasons or []),
        model_version=s.model_version, score_id=s.id) for s in res.scalars().all()]


@dataclass
class SystemActor:
    """Actor for scheduled runs. Audit rows show this id, never a real person."""
    user_id: str
    role: str = "platform_admin"
    is_platform_admin: bool = True


async def apply_policy_to_run(db: AsyncSession, run: MlScoringRun, actor: Any) -> Optional[Dict[str, Any]]:
    """Send a completed run's flags (tier != none) through the campus's active policy.

    Returns a short summary, or None when no policy is published (logged; no cases are created).
    A policy failure never undoes the scoring run.
    """
    from app.modules.policy.services import PolicyError, evaluate_risk_flags

    run_id, campus_id = run.id, run.campus_id  # read now; commits/rollbacks below expire `run`
    flags = [f for f in await flags_for_run(db, run_id) if f.tier != "none"]
    if not flags:
        return {"flags_sent": 0, "cases_created": 0, "skipped": {}}
    try:
        result = await evaluate_risk_flags(db, campus_id, flags, actor)
    except PolicyError as exc:
        await db.rollback()
        log.warning("policy not applied to run %s: %s", run_id, getattr(exc, "message", exc))
        return None
    except Exception:  # noqa: BLE001
        await db.rollback()
        log.exception("policy evaluation crashed for run %s", run_id)
        return None
    return {"evaluation_id": result.evaluation_id, "flags_sent": result.flags_received,
            "cases_created": result.cases_created, "skipped": result.skipped}
