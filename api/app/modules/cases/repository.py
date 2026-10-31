from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cases.models import Case, CaseEvent, CaseOutcome, CaseTask


class CaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, campus_id: str, case_id: str) -> Optional[Case]:
        return (await self.db.execute(
            select(Case).where(Case.id == case_id, Case.campus_id == campus_id))).scalar_one_or_none()

    async def by_flag(self, campus_id: str, flag_id: str) -> Optional[Case]:
        return (await self.db.execute(
            select(Case).where(Case.campus_id == campus_id, Case.flag_id == flag_id))).scalar_one_or_none()

    async def list(self, campus_id: str, state: Optional[str] = None, limit: int = 100) -> List[Case]:
        q = select(Case).where(Case.campus_id == campus_id).order_by(Case.created_at.desc()).limit(limit)
        if state:
            q = q.where(Case.state == state)
        return list((await self.db.execute(q)).scalars())

    async def events(self, campus_id: str, case_id: str) -> List[CaseEvent]:
        q = select(CaseEvent).where(CaseEvent.campus_id == campus_id, CaseEvent.case_id == case_id)
        return list((await self.db.execute(q.order_by(CaseEvent.created_at, CaseEvent.id))).scalars())

    async def task(self, campus_id: str, task_id: str) -> Optional[CaseTask]:
        return (await self.db.execute(
            select(CaseTask).where(CaseTask.id == task_id, CaseTask.campus_id == campus_id))).scalar_one_or_none()

    async def tasks(self, campus_id: str, case_id: str) -> List[CaseTask]:
        q = select(CaseTask).where(CaseTask.campus_id == campus_id, CaseTask.case_id == case_id)
        return list((await self.db.execute(q.order_by(CaseTask.created_at))).scalars())

    async def outcome(self, case_id: str, cycle: int) -> Optional[CaseOutcome]:
        return (await self.db.execute(
            select(CaseOutcome).where(CaseOutcome.case_id == case_id, CaseOutcome.cycle == cycle))).scalar_one_or_none()

    async def outcome_counts(self, campus_id: str) -> List[dict]:
        """Outcome counts per (intervention, reason-code pattern): what Meko promotion relies on."""
        q = (select(CaseOutcome.intervention_id, CaseOutcome.reason_pattern, CaseOutcome.outcome, func.count())
             .where(CaseOutcome.campus_id == campus_id)
             .group_by(CaseOutcome.intervention_id, CaseOutcome.reason_pattern, CaseOutcome.outcome))
        rows: dict = {}
        for iid, pattern, outcome, n in (await self.db.execute(q)).all():
            r = rows.setdefault((iid, pattern), {"intervention_id": iid, "reason_pattern": pattern,
                                                 "improved": 0, "no_change": 0, "worse": 0, "total": 0})
            r[outcome] = n
            r["total"] += n
        return sorted(rows.values(), key=lambda r: (-r["total"], r["intervention_id"], r["reason_pattern"]))

    async def overdue_cases(self, now: datetime) -> List[Case]:
        q = (select(Case).where(Case.state.notin_(("closed", "dismissed")), Case.due_at.is_not(None),
                                Case.due_at < now, Case.is_escalated.is_(False)).with_for_update(skip_locked=True))
        return list((await self.db.execute(q)).scalars())

    async def overdue_tasks(self, now: datetime) -> List[CaseTask]:
        q = (select(CaseTask).where(CaseTask.state.in_(("pending", "accepted", "in_progress")),
                                    CaseTask.due_at.is_not(None), CaseTask.due_at < now,
                                    CaseTask.is_escalated.is_(False)).with_for_update(skip_locked=True))
        return list((await self.db.execute(q)).scalars())
