"""Campus aggregates computed from stored rows only (FR-ANA-01), with small-cell suppression
(FR-ANA-02). Nothing here returns an identifiable record (FR-ANA-03)."""
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cases.models import Case, CaseEvent, FollowUp, Intervention, InterventionCatalogue, InterventionOutcome
from app.modules.identity.models import User
from app.shared.enums import CaseState, map_status_to_state
from app.shared.privacy import MIN_CELL_SIZE_ANALYTICS, suppress_distribution
from app.shared.utils import utc_now

TERMINAL = {CaseState.CLOSED, CaseState.DISMISSED}
CONTACT_EVENTS = ("CONTACT_ATTEMPTED", "SUPPORT_STARTED")
AGE_BUCKETS = [("0-7 days", 0, 7), ("8-14 days", 8, 14), ("15-30 days", 15, 30), ("31+ days", 31, None)]


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class AnalyticsService:
    @staticmethod
    async def case_summary(db: AsyncSession, campus_id: str, minimum: int = MIN_CELL_SIZE_ANALYTICS,
                           now: Optional[datetime] = None) -> Dict[str, Any]:
        now = now or utc_now()
        res = await db.execute(select(Case.status, Case.created_at, Case.assigned_counsellor_id).where(Case.campus_id == campus_id))
        rows = res.all()
        by_state: Dict[str, int] = {s.value: 0 for s in CaseState}
        ages: Dict[str, int] = {b[0]: 0 for b in AGE_BUCKETS}
        owners: Dict[Optional[str], int] = {}
        open_total = 0
        for status, created_at, owner in rows:
            state = map_status_to_state(status)
            by_state[state.value] += 1
            if state in TERMINAL:
                continue
            open_total += 1
            age = (now - _aware(created_at)).days
            for label, lo, hi in AGE_BUCKETS:
                if age >= lo and (hi is None or age <= hi):
                    ages[label] += 1
                    break
            owners[owner] = owners.get(owner, 0) + 1
        names: Dict[str, str] = {}
        real_ids = [o for o in owners if o]
        if real_ids:
            nres = await db.execute(select(User.id, User.full_name).where(User.id.in_(real_ids)))
            names = {i: n for i, n in nres.all()}
        owner_counts = {(names.get(o, "unknown") if o else "unassigned"): n for o, n in owners.items()}
        # Owner workload is staff data, but a single-case owner cell is still a one-student fact.
        return {
            "min_cell_size": minimum,
            "total_cases": len(rows),
            "open_cases": open_total,
            "by_state": suppress_distribution(by_state, minimum),
            "open_by_age": suppress_distribution(ages, minimum),
            "open_by_owner": suppress_distribution(owner_counts, minimum),
        }

    @staticmethod
    async def intervention_outcomes(db: AsyncSession, campus_id: str, minimum: int = MIN_CELL_SIZE_ANALYTICS) -> Dict[str, Any]:
        res = await db.execute(
            select(InterventionOutcome.completion_status, func.count())
            .where(InterventionOutcome.campus_id == campus_id).group_by(InterventionOutcome.completion_status)
        )
        by_status = {s: n for s, n in res.all()}
        cres = await db.execute(
            select(InterventionCatalogue.name, InterventionOutcome.completion_status, func.count())
            .join(Intervention, Intervention.catalogue_id == InterventionCatalogue.id)
            .join(InterventionOutcome, InterventionOutcome.intervention_id == Intervention.id)
            .where(InterventionOutcome.campus_id == campus_id)
            .group_by(InterventionCatalogue.name, InterventionOutcome.completion_status)
        )
        per_catalogue: Dict[str, Dict[str, int]] = {}
        for name, st, n in cres.all():
            per_catalogue.setdefault(name, {})[st] = n
        total_interventions = int(await db.scalar(select(func.count()).select_from(Intervention).where(Intervention.campus_id == campus_id)) or 0)
        out_catalogue = []
        for name, sts in sorted(per_catalogue.items()):
            total = sum(sts.values())
            if total < minimum:
                out_catalogue.append({"intervention": "suppressed", "total": None, "outcomes": [], "suppressed": True})
            else:
                out_catalogue.append({"intervention": name, "total": total, "suppressed": False,
                                      "outcomes": suppress_distribution(sts, minimum)})
        return {
            "min_cell_size": minimum,
            "interventions_total": total_interventions,
            "outcomes_recorded": sum(by_status.values()),
            "by_completion_status": suppress_distribution(by_status, minimum),
            "by_intervention": out_catalogue,
        }

    @staticmethod
    async def time_to_first_contact(db: AsyncSession, campus_id: str, minimum: int = MIN_CELL_SIZE_ANALYTICS) -> Dict[str, Any]:
        first = (
            select(CaseEvent.case_id.label("case_id"), func.min(CaseEvent.created_at).label("first_at"))
            .where(CaseEvent.campus_id == campus_id, CaseEvent.event_type.in_(CONTACT_EVENTS))
            .group_by(CaseEvent.case_id).subquery()
        )
        res = await db.execute(
            select(Case.created_at, first.c.first_at).join(first, first.c.case_id == Case.id).where(Case.campus_id == campus_id)
        )
        hours = [max((_aware(f) - _aware(c)).total_seconds() / 3600, 0.0) for c, f in res.all()]
        total_cases = int(await db.scalar(select(func.count()).select_from(Case).where(Case.campus_id == campus_id)) or 0)
        n = len(hours)
        out: Dict[str, Any] = {"min_cell_size": minimum, "cases_with_contact": n if n >= minimum else None,
                               "suppressed": n < minimum, "median_hours": None, "mean_hours": None, "p90_hours": None}
        if n >= minimum:
            out["median_hours"] = round(statistics.median(hours), 1)
            out["mean_hours"] = round(statistics.fmean(hours), 1)
            out["p90_hours"] = round(sorted(hours)[min(n - 1, int(0.9 * n))], 1)
            out["contact_rate"] = round(n / total_cases, 3) if total_cases else None
        return out

    @staticmethod
    async def followup_completion(db: AsyncSession, campus_id: str, minimum: int = MIN_CELL_SIZE_ANALYTICS,
                                  now: Optional[datetime] = None) -> Dict[str, Any]:
        now = now or utc_now()
        res = await db.execute(select(FollowUp.status, FollowUp.scheduled_at, FollowUp.completed_at).where(FollowUp.campus_id == campus_id))
        due = completed = on_time = overdue = upcoming = 0
        for st, sched, done in res.all():
            sched = _aware(sched)
            if st == "completed":
                due += 1
                completed += 1
                if done and _aware(done) <= sched + timedelta(days=1):
                    on_time += 1
            elif sched <= now:
                due += 1
                overdue += 1
            else:
                upcoming += 1
        counts = {"completed": completed, "overdue": overdue, "upcoming": upcoming}
        out: Dict[str, Any] = {"min_cell_size": minimum, "by_status": suppress_distribution(counts, minimum),
                               "suppressed": due < minimum, "completion_rate": None, "on_time_rate": None}
        if due >= minimum:
            out["completion_rate"] = round(completed / due, 3)
            out["on_time_rate"] = round(on_time / completed, 3) if completed >= minimum else None
        return out

    @staticmethod
    async def overview(db: AsyncSession, campus_id: str, minimum: int = MIN_CELL_SIZE_ANALYTICS) -> Dict[str, Any]:
        return {
            "cases": await AnalyticsService.case_summary(db, campus_id, minimum),
            "interventions": await AnalyticsService.intervention_outcomes(db, campus_id, minimum),
            "time_to_first_contact": await AnalyticsService.time_to_first_contact(db, campus_id, minimum),
            "followups": await AnalyticsService.followup_completion(db, campus_id, minimum),
        }
