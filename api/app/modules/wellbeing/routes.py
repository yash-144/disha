from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.core.exceptions import EntityNotFoundError
from app.core.permissions import Role
from app.modules.rewards.permissions import current_student
from app.modules.wellbeing.models import PulseQuestionnaire
from app.modules.wellbeing.schemas import (
    AggregateResponse, CurrentPulseResponse, PeriodCreate, PeriodResponse, PulseStatusResponse,
    PulseSubmissionCreate, PulseSubmissionResponse, QuestionnaireCreate, QuestionnaireResponse, TrendPoint,
)
from app.modules.wellbeing.services import WellbeingService, band_of

router = APIRouter()

admin = require_role(Role.INSTITUTION_ADMIN)
# Aggregates only (blueprint 04 `pulse.aggregate`): hod, counsellor, leadership, institution_admin.
aggregate_viewer = require_role(Role.INSTITUTION_ADMIN, Role.HOD, Role.COUNSELLOR, Role.LEADERSHIP)


@router.post("/pulse/questionnaires", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(payload: QuestionnaireCreate, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    q = await WellbeingService.create_questionnaire(db, ctx.campus_id, ctx.user_id, payload)
    await db.commit()
    return q


@router.get("/pulse/questionnaires", response_model=List[QuestionnaireResponse])
async def list_questionnaires(ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    return await WellbeingService.list_questionnaires(db, ctx.campus_id)


@router.post("/pulse/periods", response_model=PeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_period(payload: PeriodCreate, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    p = await WellbeingService.create_period(db, ctx.campus_id, ctx.user_id, payload)
    await db.commit()
    return p


@router.get("/pulse/periods", response_model=List[PeriodResponse])
async def list_periods(ctx: TenancyContext = Depends(aggregate_viewer), db: AsyncSession = Depends(get_db)):
    return await WellbeingService.list_periods(db, ctx.campus_id)


@router.get("/pulse/current", response_model=CurrentPulseResponse)
async def current(student=Depends(current_student), db: AsyncSession = Depends(get_db)):
    period = await WellbeingService.current_period(db, student.campus_id)
    if not period:
        raise EntityNotFoundError("Open pulse period", student.campus_id)
    q = await db.get(PulseQuestionnaire, period.questionnaire_id)
    return CurrentPulseResponse(
        period=period, questionnaire=q,
        already_submitted=await WellbeingService.has_submitted(db, student.id, period.id),
    )


@router.post("/pulse/submissions", response_model=PulseSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit(payload: PulseSubmissionCreate, student=Depends(current_student), db: AsyncSession = Depends(get_db)):
    result = await WellbeingService.submit(db, student, payload)
    await db.commit()
    sub = result["submission"]
    return PulseSubmissionResponse(
        id=sub.id, period_id=sub.period_id, index_score=sub.index_score, band=band_of(sub.index_score),
        dimension_scores=sub.dimension_scores, points_awarded=result["points"], submitted_at=sub.submitted_at,
    )


@router.get("/pulse/status", response_model=PulseStatusResponse)
async def pulse_status(student=Depends(current_student), db: AsyncSession = Depends(get_db)):
    """Caller's own completion only (never 'anyone has submitted')."""
    period = await WellbeingService.current_period(db, student.campus_id)
    if not period:
        return PulseStatusResponse(period_id=None, completed=False)
    return PulseStatusResponse(period_id=period.id, completed=await WellbeingService.has_submitted(db, student.id, period.id))


@router.get("/pulse/aggregate", response_model=AggregateResponse)
async def aggregate(period_id: str = Query(...), ctx: TenancyContext = Depends(aggregate_viewer), db: AsyncSession = Depends(get_db)):
    return await WellbeingService.aggregate(db, ctx.campus_id, period_id)


@router.get("/pulse/trends", response_model=List[TrendPoint])
async def trends(ctx: TenancyContext = Depends(aggregate_viewer), db: AsyncSession = Depends(get_db)):
    return await WellbeingService.trends(db, ctx.campus_id)
