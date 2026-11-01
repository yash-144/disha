"""Wellbeing pulse (blueprint 10 §2-3). Scoring runs here, never in the browser (PUL-06)."""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException, EntityNotFoundError
from app.modules.audit.services import AuditService
from app.modules.rewards.services import RewardsService
from app.modules.roster.models import Student
from app.modules.wellbeing.models import PulsePeriod, PulseQuestionnaire, PulseSubmission
from app.shared.privacy import MIN_RESPONDENTS_PULSE
from app.shared.utils import utc_now

PULSE_POINTS_ACTIVITY = "weekly_pulse"  # fixed points, independent of answers (PTS-04)


class WellbeingError(DishaBaseException):
    pass


# ---- scoring (pure) ----------------------------------------------------------------------

def normalise(r: Any) -> Optional[float]:
    """1..5 integer -> 0..100; anything else is excluded (None), never 0 or 50."""
    if isinstance(r, bool) or not isinstance(r, int) or not 1 <= r <= 5:
        return None
    return (r - 1) / 4 * 100


def _mean(values: List[float]) -> Optional[float]:
    return round(sum(values) / len(values), 1) if values else None


def score_responses(questions: List[Dict[str, Any]], responses: Dict[str, Any]):
    by_dim: Dict[str, List[float]] = {}
    for q in questions:
        by_dim.setdefault(q["dimension"], [])
        n = normalise(responses.get(q["key"]))
        if n is not None:
            by_dim[q["dimension"]].append(n)
    dims = {d: _mean(v) for d, v in by_dim.items()}
    return dims, index_of(dims)


def index_of(dims: Dict[str, Optional[float]]) -> Optional[float]:
    vals = [v for v in dims.values() if v is not None]
    return _mean(vals)


def band_of(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 80:
        return "strong"
    if score >= 65:
        return "positive"
    if score >= 50:
        return "needs_attention"
    return "priority_review"


# ---- reflection encryption (PUL-04) ------------------------------------------------------

def _fernet():
    key = os.environ.get("DISHA_REFLECTION_KEY")
    if not key:
        return None
    from cryptography.fernet import Fernet
    return Fernet(key.encode())


def encrypt_reflection(text: str) -> str:
    f = _fernet()
    if f is None:
        raise WellbeingError("Reflections are disabled until DISHA_REFLECTION_KEY is configured", 503)
    return f.encrypt(text.encode("utf-8")).decode("ascii")


class WellbeingService:
    # ---- admin configuration -------------------------------------------------------------
    @staticmethod
    async def create_questionnaire(db: AsyncSession, campus_id: str, actor_id: str, data) -> PulseQuestionnaire:
        q = PulseQuestionnaire(
            campus_id=campus_id, version_key=data.version_key, created_by=actor_id,
            questions=[x.model_dump() for x in data.questions],
        )
        try:
            async with db.begin_nested():
                db.add(q)
                await db.flush()
        except IntegrityError:
            raise WellbeingError("Questionnaire version already exists", 409)
        await AuditService.record_event(db, actor_id, campus_id, "pulse_questionnaire", q.id, "PULSE_QUESTIONNAIRE_CREATED",
                                        {"version_key": q.version_key, "questions": len(q.questions)})
        return q

    @staticmethod
    async def list_questionnaires(db: AsyncSession, campus_id: str) -> List[PulseQuestionnaire]:
        res = await db.execute(select(PulseQuestionnaire).where(PulseQuestionnaire.campus_id == campus_id)
                               .order_by(PulseQuestionnaire.created_at.desc()))
        return list(res.scalars().all())

    @staticmethod
    async def create_period(db: AsyncSession, campus_id: str, actor_id: str, data) -> PulsePeriod:
        if data.ends_at <= data.starts_at:
            raise WellbeingError("Period must end after it starts", 422)
        q = await db.scalar(select(PulseQuestionnaire.id).where(
            PulseQuestionnaire.id == data.questionnaire_id, PulseQuestionnaire.campus_id == campus_id))
        if not q:
            raise EntityNotFoundError("PulseQuestionnaire", data.questionnaire_id)
        p = PulsePeriod(campus_id=campus_id, questionnaire_id=q, label=data.label,
                        starts_at=data.starts_at, ends_at=data.ends_at, created_by=actor_id)
        try:
            async with db.begin_nested():
                db.add(p)
                await db.flush()
        except IntegrityError:
            raise WellbeingError("Period label already exists", 409)
        await AuditService.record_event(db, actor_id, campus_id, "pulse_period", p.id, "PULSE_PERIOD_CREATED", {"label": p.label})
        return p

    @staticmethod
    async def list_periods(db: AsyncSession, campus_id: str) -> List[PulsePeriod]:
        res = await db.execute(select(PulsePeriod).where(PulsePeriod.campus_id == campus_id).order_by(PulsePeriod.starts_at.desc()))
        return list(res.scalars().all())

    @staticmethod
    async def current_period(db: AsyncSession, campus_id: str, now: Optional[datetime] = None) -> Optional[PulsePeriod]:
        now = now or utc_now()
        res = await db.execute(select(PulsePeriod).where(
            PulsePeriod.campus_id == campus_id, PulsePeriod.starts_at <= now, PulsePeriod.ends_at > now
        ).order_by(PulsePeriod.starts_at.desc()))
        return res.scalars().first()

    # ---- student -------------------------------------------------------------------------
    @staticmethod
    async def has_submitted(db: AsyncSession, student_id: str, period_id: str) -> bool:
        return bool(await db.scalar(select(PulseSubmission.id).where(
            PulseSubmission.student_id == student_id, PulseSubmission.period_id == period_id)))

    @staticmethod
    async def submit(db: AsyncSession, student: Student, data) -> Dict[str, Any]:
        period = await WellbeingService.current_period(db, student.campus_id)
        if not period:
            raise WellbeingError("No pulse period is open", 409)
        if await WellbeingService.has_submitted(db, student.id, period.id):
            raise WellbeingError("Pulse already submitted for this period", 409)
        q = await db.get(PulseQuestionnaire, period.questionnaire_id)
        dims, index = score_responses(q.questions, data.responses)
        if index is None:
            raise WellbeingError("No valid responses (each must be an integer 1-5)", 422)
        cipher = encrypt_reflection(data.reflection) if data.reflection else None
        sub = PulseSubmission(
            campus_id=student.campus_id, student_id=student.id, period_id=period.id, questionnaire_id=q.id,
            responses={k: v for k, v in data.responses.items() if normalise(v) is not None},
            dimension_scores=dims, index_score=index, department=student.department, reflection_ciphertext=cipher,
        )
        try:
            async with db.begin_nested():
                db.add(sub)
                await db.flush()
        except IntegrityError:
            raise WellbeingError("Pulse already submitted for this period", 409)
        # Points never depend on answers (PTS-04): same activity, same amount, keyed by period.
        entry, _ = await RewardsService.award(db, student.campus_id, student.id, PULSE_POINTS_ACTIVITY, period.id, None)
        return {"submission": sub, "points": entry.points}

    # ---- aggregates ----------------------------------------------------------------------
    @staticmethod
    async def eligible_count(db: AsyncSession, campus_id: str) -> int:
        return int(await db.scalar(select(func.count()).select_from(Student).where(
            Student.campus_id == campus_id, Student.is_active.is_(True))) or 0)

    @staticmethod
    def _aggregate_rows(rows: List[PulseSubmission]):
        dim_vals: Dict[str, List[float]] = {}
        for r in rows:
            for d, v in (r.dimension_scores or {}).items():
                dim_vals.setdefault(d, [])
                if v is not None:
                    dim_vals[d].append(v)
        dims = {d: _mean(v) for d, v in dim_vals.items()}
        return dims, index_of(dims)

    @staticmethod
    async def aggregate(db: AsyncSession, campus_id: str, period_id: str, minimum: int = MIN_RESPONDENTS_PULSE) -> Dict[str, Any]:
        period = await db.scalar(select(PulsePeriod).where(PulsePeriod.id == period_id, PulsePeriod.campus_id == campus_id))
        if not period:
            raise EntityNotFoundError("PulsePeriod", period_id)
        res = await db.execute(select(PulseSubmission).where(
            PulseSubmission.campus_id == campus_id, PulseSubmission.period_id == period_id))
        rows = list(res.scalars().all())
        eligible = await WellbeingService.eligible_count(db, campus_id)
        n = len(rows)
        out: Dict[str, Any] = {
            "period_id": period_id, "response_count": n, "eligible_count": eligible,
            "participation_rate": round(n / eligible, 3) if eligible else None,
            "min_respondents": minimum, "suppressed": n < minimum, "by_department": [],
            "index_score": None, "band": None, "dimension_scores": None,
        }
        if n < minimum:
            out.update(response_count=None, participation_rate=None)  # a count below the threshold is itself small-cell data
            return out  # PUL-08: no scores below the threshold
        dims, index = WellbeingService._aggregate_rows(rows)
        out.update(dimension_scores=dims, index_score=index, band=band_of(index))
        groups: Dict[str, List[PulseSubmission]] = {}
        for r in rows:
            groups.setdefault(r.department or "unassigned", []).append(r)
        hidden_other = 0
        for dept, grp in sorted(groups.items()):
            if len(grp) < minimum:
                hidden_other += 1
                out["by_department"].append({"department": dept, "response_count": None, "suppressed": True,
                                             "index_score": None, "band": None})
                continue
            _, gi = WellbeingService._aggregate_rows(grp)
            out["by_department"].append({"department": dept, "response_count": len(grp), "suppressed": False,
                                         "index_score": gi, "band": band_of(gi)})
        if hidden_other == 1:  # complementary suppression: the hidden count is otherwise total minus the rest
            shown = [d for d in out["by_department"] if not d["suppressed"]]
            if shown:
                min(shown, key=lambda d: d["response_count"])["response_count"] = None
        # Hide department names too when suppressed, so a small group is not named with its size class.
        for d in out["by_department"]:
            if d["suppressed"]:
                d["department"] = "suppressed"
        return out

    @staticmethod
    async def trends(db: AsyncSession, campus_id: str, minimum: int = MIN_RESPONDENTS_PULSE) -> List[Dict[str, Any]]:
        periods = sorted(await WellbeingService.list_periods(db, campus_id), key=lambda p: p.starts_at)
        points: List[Dict[str, Any]] = []
        prev: Optional[float] = None
        for p in periods:
            res = await db.execute(select(PulseSubmission).where(
                PulseSubmission.campus_id == campus_id, PulseSubmission.period_id == p.id))
            rows = list(res.scalars().all())
            n = len(rows)
            if n < minimum:
                points.append({"period_id": p.id, "label": p.label, "starts_at": p.starts_at, "suppressed": True,
                               "response_count": None, "index_score": None, "change": None})
                prev = None
                continue
            _, idx = WellbeingService._aggregate_rows(rows)
            change = round(idx - prev, 1) if idx is not None and prev is not None else None
            points.append({"period_id": p.id, "label": p.label, "starts_at": p.starts_at, "suppressed": False,
                           "response_count": n, "index_score": idx, "change": change})
            prev = idx
        return points
