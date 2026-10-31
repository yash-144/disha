"""Intervention catalogue (``router``, mounted at /api/v1/interventions) and the case-scoped
interventions / outcome / follow-up routes (``case_router``, mounted at /api/v1/cases next to the cases router).
"""
from typing import List

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, get_tenancy_context, require_role
from app.core.permissions import STAFF_ROLES
from app.modules.interventions.permissions import CASE_WORK_ROLES, CASE_VIEW_ROLES, CATALOGUE_ADMIN_ROLES
from app.modules.interventions.schemas import (
    CatalogueCreate,
    CatalogueItem,
    CatalogueUpdate,
    FollowUpCancel,
    FollowUpComplete,
    FollowUpCreate,
    FollowUpNoteCreate,
    FollowUpOut,
    FollowUpReschedule,
    InterventionCreate,
    InterventionOut,
    InterventionProgressUpdate,
    OutcomeCreate,
    OutcomeOut,
)
from app.modules.interventions.services import (
    CatalogueService,
    FollowUpService,
    InterventionService,
)
from app.shared.idempotency import verify_idempotency_key
from app.shared.idempotency_store import run_idempotent

router = APIRouter(tags=["Interventions"])
case_router = APIRouter(tags=["Case interventions and follow-ups"])

require_staff = require_role(*STAFF_ROLES)
require_catalogue_admin = require_role(*CATALOGUE_ADMIN_ROLES)
require_case_work = require_role(*CASE_WORK_ROLES)
require_case_view = require_role(*CASE_VIEW_ROLES)


# ---------------------------------------------------------------- catalogue
@router.get("/catalog", response_model=List[CatalogueItem])
async def list_catalogue(
    include_inactive: bool = Query(False),
    ctx: TenancyContext = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Active interventions available on the campus. Admins may include inactive entries."""
    inactive = include_inactive and ctx.role in CATALOGUE_ADMIN_ROLES
    return [CatalogueItem.model_validate(i) for i in await CatalogueService.list(db, ctx.campus_id, inactive)]


@router.post("/catalog", response_model=CatalogueItem, status_code=status.HTTP_201_CREATED)
async def create_catalogue_item(
    payload: CatalogueCreate,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_catalogue_admin),
    db: AsyncSession = Depends(get_db),
):
    async def produce():
        return CatalogueItem.model_validate(await CatalogueService.create(db, ctx, payload))

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope="catalog.create", body=payload.model_dump(), produce=produce,
    )


@router.patch("/catalog/{item_id}", response_model=CatalogueItem)
async def update_catalogue_item(
    payload: CatalogueUpdate,
    item_id: str = Path(...),
    ctx: TenancyContext = Depends(require_catalogue_admin),
    db: AsyncSession = Depends(get_db),
):
    item = await CatalogueService.update(db, ctx, item_id, payload)
    await db.commit()
    return CatalogueItem.model_validate(item)


# ------------------------------------------------------------ interventions
@case_router.get("/{case_id}/interventions", response_model=List[InterventionOut])
async def list_case_interventions(
    case_id: str = Path(...), ctx: TenancyContext = Depends(require_case_view), db: AsyncSession = Depends(get_db)
):
    return await InterventionService.list_for_case(db, ctx, case_id)


@case_router.post("/{case_id}/interventions", response_model=InterventionOut, status_code=status.HTTP_201_CREATED)
async def create_case_intervention(
    payload: InterventionCreate,
    case_id: str = Path(...),
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    async def produce():
        return await InterventionService.create(db, ctx, case_id, payload)

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope=f"case.{case_id}.intervention.create", body=payload.model_dump(), produce=produce,
    )


@case_router.patch("/{case_id}/interventions/{intervention_id}", response_model=InterventionOut)
async def update_case_intervention(
    payload: InterventionProgressUpdate,
    case_id: str = Path(...),
    intervention_id: str = Path(...),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    out = await InterventionService.update_progress(db, ctx, case_id, intervention_id, payload)
    await db.commit()
    return out


@case_router.post("/{case_id}/outcome", response_model=OutcomeOut, status_code=status.HTTP_201_CREATED)
async def record_case_outcome(
    payload: OutcomeCreate,
    case_id: str = Path(...),
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    """Record the outcome of an intervention. Moving the case to ``outcome_reviewed`` stays a
    ``POST /cases/{id}/transition``, whose guard now finds this row."""
    async def produce():
        return await InterventionService.record_outcome(db, ctx, case_id, payload)

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope=f"case.{case_id}.outcome", body=payload.model_dump(), produce=produce,
    )


# ---------------------------------------------------------------- follow-ups
@case_router.get("/{case_id}/follow-ups", response_model=List[FollowUpOut])
async def list_case_followups(
    case_id: str = Path(...), ctx: TenancyContext = Depends(require_case_view), db: AsyncSession = Depends(get_db)
):
    return await FollowUpService.list_for_case(db, ctx, case_id)


@case_router.post("/{case_id}/follow-ups", response_model=FollowUpOut, status_code=status.HTTP_201_CREATED)
async def create_case_followup(
    payload: FollowUpCreate,
    case_id: str = Path(...),
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    async def produce():
        return await FollowUpService.create(db, ctx, case_id, payload)

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope=f"case.{case_id}.followup.create", body=payload.model_dump(), produce=produce,
    )


@case_router.patch("/{case_id}/follow-ups/{followup_id}", response_model=FollowUpOut)
async def reschedule_case_followup(
    payload: FollowUpReschedule,
    case_id: str = Path(...),
    followup_id: str = Path(...),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    out = await FollowUpService.reschedule(db, ctx, case_id, followup_id, payload)
    await db.commit()
    return out


@case_router.post("/{case_id}/follow-ups/{followup_id}/complete", response_model=FollowUpOut)
async def complete_case_followup(
    payload: FollowUpComplete,
    case_id: str = Path(...),
    followup_id: str = Path(...),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    out = await FollowUpService.complete(db, ctx, case_id, followup_id, payload)
    await db.commit()
    return out


@case_router.post("/{case_id}/follow-ups/{followup_id}/cancel", response_model=FollowUpOut)
async def cancel_case_followup(
    payload: FollowUpCancel,
    case_id: str = Path(...),
    followup_id: str = Path(...),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    out = await FollowUpService.cancel(db, ctx, case_id, followup_id, payload)
    await db.commit()
    return out


@case_router.post("/{case_id}/follow-ups/{followup_id}/notes", response_model=FollowUpOut,
                  status_code=status.HTTP_201_CREATED)
async def add_followup_note(
    payload: FollowUpNoteCreate,
    case_id: str = Path(...),
    followup_id: str = Path(...),
    ctx: TenancyContext = Depends(require_case_work),
    db: AsyncSession = Depends(get_db),
):
    out = await FollowUpService.add_note(db, ctx, case_id, followup_id, payload)
    await db.commit()
    return out
