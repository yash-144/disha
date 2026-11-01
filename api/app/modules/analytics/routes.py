from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.core.permissions import Role
from app.modules.analytics.services import AnalyticsService

router = APIRouter()

# analytics.cohort (blueprint 04): institution_admin and counsellor, plus hod / leadership (aggregates only).
viewer = require_role(Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.HOD, Role.LEADERSHIP)


@router.get("/overview")
async def overview(ctx: TenancyContext = Depends(viewer), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService.overview(db, ctx.campus_id)


@router.get("/cases/summary")
async def case_summary(ctx: TenancyContext = Depends(viewer), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService.case_summary(db, ctx.campus_id)


@router.get("/interventions/outcomes")
async def intervention_outcomes(ctx: TenancyContext = Depends(viewer), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService.intervention_outcomes(db, ctx.campus_id)


@router.get("/cases/time-to-first-contact")
async def time_to_first_contact(ctx: TenancyContext = Depends(viewer), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService.time_to_first_contact(db, ctx.campus_id)


@router.get("/followups/completion")
async def followup_completion(ctx: TenancyContext = Depends(viewer), db: AsyncSession = Depends(get_db)):
    return await AnalyticsService.followup_completion(db, ctx.campus_id)
