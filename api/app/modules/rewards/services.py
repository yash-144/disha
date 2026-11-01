"""Points ledger and redemptions (blueprint 10 §4-5: PTS-01..04, RED-01..03)."""
from typing import List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException, EntityNotFoundError
from app.modules.audit.services import AuditService
from app.modules.rewards.models import LedgerEntry, Redemption, RewardItem
from app.modules.roster.models import Student
from app.shared.utils import utc_now

# Activity catalogue from blueprint 10 §4 (business rules, not demo data).
# Points are fixed per activity and never depend on pulse answers (PTS-04).
ACTIVITIES = {
    "weekly_pulse": (10, "once per reporting week"),
    "daily_micro_challenge": (5, "once per challenge"),
    "approved_workshop": (15, "once per event"),
    "student_development": (10, "once per activity"),
    "verified_learning": (10, "once per activity"),
    "campus_improvement": (20, "once per initiative"),
}
SYSTEM_ONLY_ACTIVITIES = {"weekly_pulse"}  # PTS-03: only the system awards pulse points

REDEMPTION_TRANSITIONS = {
    "requested": {"approved", "fulfilled", "rejected"},
    "approved": {"fulfilled", "rejected"},
}


class RewardsError(DishaBaseException):
    pass


class RewardsService:
    @staticmethod
    async def balance(db: AsyncSession, campus_id: str, student_id: str) -> int:
        total = await db.scalar(
            select(func.coalesce(func.sum(LedgerEntry.points), 0)).where(
                LedgerEntry.campus_id == campus_id, LedgerEntry.student_id == student_id
            )
        )
        return int(total or 0)

    @staticmethod
    async def history(db: AsyncSession, campus_id: str, student_id: str, limit: int = 50, offset: int = 0) -> List[LedgerEntry]:
        res = await db.execute(
            select(LedgerEntry).where(LedgerEntry.campus_id == campus_id, LedgerEntry.student_id == student_id)
            .order_by(LedgerEntry.created_at.desc(), LedgerEntry.id.desc()).limit(limit).offset(offset)
        )
        return list(res.scalars().all())

    @staticmethod
    async def award(
        db: AsyncSession, campus_id: str, student_id: str, activity_key: str, source_ref: str,
        created_by: Optional[str], note: Optional[str] = None,
    ) -> Tuple[LedgerEntry, bool]:
        """Idempotent award. Returns (entry, created). A repeat claim returns the original entry."""
        if activity_key not in ACTIVITIES:
            raise RewardsError(f"Unknown activity '{activity_key}'", 422)
        student = await db.scalar(select(Student.id).where(Student.id == student_id, Student.campus_id == campus_id))
        if not student:
            raise EntityNotFoundError("Student", student_id)
        key = f"award:{student_id}:{activity_key}:{source_ref}"
        existing = await db.scalar(
            select(LedgerEntry).where(LedgerEntry.campus_id == campus_id, LedgerEntry.idempotency_key == key)
        )
        if existing:
            return existing, False
        entry = LedgerEntry(
            campus_id=campus_id, student_id=student_id, entry_type="award", activity_key=activity_key,
            source_ref=source_ref, points=ACTIVITIES[activity_key][0], idempotency_key=key,
            created_by=created_by, note=note,
        )
        try:
            async with db.begin_nested():
                db.add(entry)
                await db.flush()
        except IntegrityError:  # lost a race with a concurrent identical claim
            existing = await db.scalar(
                select(LedgerEntry).where(LedgerEntry.campus_id == campus_id, LedgerEntry.idempotency_key == key)
            )
            return existing, False
        if created_by:
            await AuditService.record_event(
                db, created_by, campus_id, "reward_ledger", entry.id, "POINTS_AWARDED",
                {"activity_key": activity_key, "points": entry.points},
            )
        return entry, True

    # ---- catalogue -----------------------------------------------------------------------
    @staticmethod
    async def list_items(db: AsyncSession, campus_id: str, include_unavailable: bool = False) -> List[RewardItem]:
        stmt = select(RewardItem).where(RewardItem.campus_id == campus_id)
        if not include_unavailable:
            stmt = stmt.where(RewardItem.is_available.is_(True))
        res = await db.execute(stmt.order_by(RewardItem.cost_points, RewardItem.name))
        return list(res.scalars().all())

    @staticmethod
    async def create_item(db: AsyncSession, campus_id: str, actor_id: str, data) -> RewardItem:
        item = RewardItem(campus_id=campus_id, **data.model_dump())
        db.add(item)
        await db.flush()
        await AuditService.record_event(db, actor_id, campus_id, "reward_item", item.id, "REWARD_ITEM_CREATED",
                                        {"cost_points": item.cost_points, "stock": item.stock})
        return item

    @staticmethod
    async def update_item(db: AsyncSession, campus_id: str, actor_id: str, item_id: str, data) -> RewardItem:
        item = await db.scalar(select(RewardItem).where(RewardItem.id == item_id, RewardItem.campus_id == campus_id))
        if not item:
            raise EntityNotFoundError("RewardItem", item_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(item, k, v)
        await db.flush()
        await AuditService.record_event(db, actor_id, campus_id, "reward_item", item.id, "REWARD_ITEM_UPDATED",
                                        {"fields": sorted(data.model_dump(exclude_unset=True))})
        return item

    # ---- redemption ----------------------------------------------------------------------
    @staticmethod
    async def redeem(db: AsyncSession, campus_id: str, student_id: str, item_id: str, idempotency_key: str) -> Tuple[Redemption, bool]:
        """RED-01: lock, check stock and balance, write negative ledger entry + redemption, decrement stock."""
        prior = await db.scalar(select(Redemption).where(
            Redemption.campus_id == campus_id, Redemption.student_id == student_id,
            Redemption.idempotency_key == idempotency_key))
        if prior:
            if prior.item_id != item_id:
                raise RewardsError("Idempotency key was already used for a different item", 409)
            return prior, False

        # Serialise this student's spending (no-op on SQLite, row lock on Postgres).
        await db.execute(select(Student.id).where(Student.id == student_id).with_for_update())
        item = await db.scalar(
            select(RewardItem).where(RewardItem.id == item_id, RewardItem.campus_id == campus_id).with_for_update()
        )
        if not item or not item.is_available:
            raise EntityNotFoundError("RewardItem", item_id)
        bal = await RewardsService.balance(db, campus_id, student_id)
        if bal < item.cost_points:
            raise RewardsError("Insufficient points balance", 422, {"balance": bal, "cost": item.cost_points})
        res = await db.execute(
            update(RewardItem).where(RewardItem.id == item.id, RewardItem.stock > 0).values(stock=RewardItem.stock - 1)
        )
        if res.rowcount == 0:
            raise RewardsError("Item is out of stock", 409)
        red = Redemption(
            campus_id=campus_id, student_id=student_id, item_id=item.id, cost_points=item.cost_points,
            status="requested", idempotency_key=idempotency_key,
        )
        db.add(red)
        await db.flush()
        db.add(LedgerEntry(
            campus_id=campus_id, student_id=student_id, entry_type="redemption", points=-item.cost_points,
            idempotency_key=f"redeem:{red.id}", reference_id=red.id, created_by=None,
        ))
        await db.flush()
        return red, True

    @staticmethod
    async def list_redemptions(db: AsyncSession, campus_id: str, student_id: Optional[str] = None,
                               status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Redemption]:
        stmt = select(Redemption).where(Redemption.campus_id == campus_id)
        if student_id:
            stmt = stmt.where(Redemption.student_id == student_id)
        if status:
            stmt = stmt.where(Redemption.status == status)
        res = await db.execute(stmt.order_by(Redemption.created_at.desc(), Redemption.id.desc()).limit(limit).offset(offset))
        return list(res.scalars().all())

    @staticmethod
    async def update_redemption(db: AsyncSession, campus_id: str, actor_id: str, redemption_id: str,
                                new_status: str, note: Optional[str]) -> Redemption:
        """RED-03: staff fulfilment. Rejection refunds with a positive ledger entry and restocks."""
        red = await db.scalar(select(Redemption).where(Redemption.id == redemption_id, Redemption.campus_id == campus_id).with_for_update())
        if not red:
            raise EntityNotFoundError("Redemption", redemption_id)
        if new_status not in REDEMPTION_TRANSITIONS.get(red.status, set()):
            raise RewardsError(f"Cannot move redemption from '{red.status}' to '{new_status}'", 409)
        red.status = new_status
        red.handled_by = actor_id
        red.handled_at = utc_now()
        red.note = note
        if new_status == "rejected":
            db.add(LedgerEntry(
                campus_id=campus_id, student_id=red.student_id, entry_type="reversal", points=red.cost_points,
                idempotency_key=f"reversal:{red.id}", reference_id=red.id, created_by=actor_id,
            ))
            await db.execute(update(RewardItem).where(RewardItem.id == red.item_id).values(stock=RewardItem.stock + 1))
        await db.flush()
        await AuditService.record_event(db, actor_id, campus_id, "reward_redemption", red.id, "REDEMPTION_" + new_status.upper(),
                                        {"cost_points": red.cost_points})
        return red
