from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, get_tenancy_context, require_role
from app.modules.rewards.permissions import ADMIN_ROLES, AWARD_ROLES, current_student
from app.modules.rewards.schemas import (
    ActivityResponse, AwardRequest, BalanceResponse, LedgerEntryResponse, RedemptionCreate,
    RedemptionResponse, RedemptionStatusUpdate, RewardItemCreate, RewardItemResponse, RewardItemUpdate,
)
from app.modules.rewards.services import ACTIVITIES, RewardsError, RewardsService, SYSTEM_ONLY_ACTIVITIES
from app.shared.idempotency import verify_idempotency_key

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def balance(student=Depends(current_student), db: AsyncSession = Depends(get_db)):
    return BalanceResponse(student_id=student.id, balance=await RewardsService.balance(db, student.campus_id, student.id))


@router.get("/history", response_model=List[LedgerEntryResponse])
async def history(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    student=Depends(current_student), db: AsyncSession = Depends(get_db),
):
    return await RewardsService.history(db, student.campus_id, student.id, limit, offset)


@router.get("/activities", response_model=List[ActivityResponse])
async def activities(ctx: TenancyContext = Depends(get_tenancy_context)):
    return [ActivityResponse(key=k, points=p, frequency=f) for k, (p, f) in ACTIVITIES.items()]


@router.get("/catalog", response_model=List[RewardItemResponse])
async def catalog(ctx: TenancyContext = Depends(get_tenancy_context), db: AsyncSession = Depends(get_db)):
    return await RewardsService.list_items(db, ctx.campus_id)


@router.post("/catalog", response_model=RewardItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(payload: RewardItemCreate, ctx: TenancyContext = Depends(require_role(*ADMIN_ROLES)),
                      db: AsyncSession = Depends(get_db)):
    item = await RewardsService.create_item(db, ctx.campus_id, ctx.user_id, payload)
    await db.commit()
    return item


@router.patch("/catalog/{item_id}", response_model=RewardItemResponse)
async def update_item(item_id: str, payload: RewardItemUpdate, ctx: TenancyContext = Depends(require_role(*ADMIN_ROLES)),
                      db: AsyncSession = Depends(get_db)):
    item = await RewardsService.update_item(db, ctx.campus_id, ctx.user_id, item_id, payload)
    await db.commit()
    return item


@router.post("/awards", response_model=LedgerEntryResponse)
async def award(payload: AwardRequest, ctx: TenancyContext = Depends(require_role(*AWARD_ROLES)),
                db: AsyncSession = Depends(get_db)):
    if payload.activity_key in SYSTEM_ONLY_ACTIVITIES:
        raise RewardsError(f"'{payload.activity_key}' points are awarded by the system only", 403)
    entry, _ = await RewardsService.award(db, ctx.campus_id, payload.student_id, payload.activity_key,
                                          payload.source_ref, ctx.user_id, payload.note)
    await db.commit()
    return entry


@router.post("/redemptions", response_model=RedemptionResponse, status_code=status.HTTP_201_CREATED)
async def create_redemption(
    payload: RedemptionCreate, idempotency_key: str = Depends(verify_idempotency_key),
    student=Depends(current_student), db: AsyncSession = Depends(get_db),
):
    red, _ = await RewardsService.redeem(db, student.campus_id, student.id, payload.item_id, idempotency_key)
    await db.commit()
    return red


@router.get("/redemptions/mine", response_model=List[RedemptionResponse])
async def my_redemptions(student=Depends(current_student), db: AsyncSession = Depends(get_db)):
    return await RewardsService.list_redemptions(db, student.campus_id, student_id=student.id)


@router.get("/redemptions", response_model=List[RedemptionResponse])
async def list_redemptions(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_role(*ADMIN_ROLES)), db: AsyncSession = Depends(get_db),
):
    return await RewardsService.list_redemptions(db, ctx.campus_id, status=status_filter, limit=limit, offset=offset)


@router.post("/redemptions/{redemption_id}/status", response_model=RedemptionResponse)
async def update_redemption(redemption_id: str, payload: RedemptionStatusUpdate,
                            ctx: TenancyContext = Depends(require_role(*ADMIN_ROLES)), db: AsyncSession = Depends(get_db)):
    red = await RewardsService.update_redemption(db, ctx.campus_id, ctx.user_id, redemption_id, payload.status, payload.note)
    await db.commit()
    return red
