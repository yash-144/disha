from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.core.permissions import Role
from app.modules.policy.schemas import (
    DecisionResponse,
    DryRunRequest,
    EvaluationSummary,
    PolicyEvaluationResult,
    PolicyVersionCreate,
    PolicyVersionResponse,
    PolicyVersionUpdate,
)
from app.modules.policy.services import PolicyService, evaluate_risk_flags
from app.core.exceptions import EntityNotFoundError

router = APIRouter()

admin = require_role(Role.INSTITUTION_ADMIN)


@router.get("/versions", response_model=List[PolicyVersionResponse])
async def list_versions(
    status_filter: Optional[str] = Query(None, alias="status"),
    ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db),
):
    return await PolicyService.list_versions(db, ctx.campus_id, status_filter)


@router.get("/active", response_model=PolicyVersionResponse)
async def get_active(ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    pv = await PolicyService.get_active(db, ctx.campus_id)
    if not pv:
        raise EntityNotFoundError("Active policy", ctx.campus_id)
    return pv


@router.post("/versions", response_model=PolicyVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    payload: PolicyVersionCreate, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db),
):
    pv = await PolicyService.create_version(db, ctx.campus_id, ctx.user_id, payload)
    await db.commit()
    return pv


@router.get("/versions/{version_id}", response_model=PolicyVersionResponse)
async def get_version(version_id: str, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    return await PolicyService.get_version(db, ctx.campus_id, version_id)


@router.patch("/versions/{version_id}", response_model=PolicyVersionResponse)
async def update_version(
    version_id: str, payload: PolicyVersionUpdate,
    ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db),
):
    pv = await PolicyService.update_version(db, ctx.campus_id, ctx.user_id, version_id, payload)
    await db.commit()
    return pv


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(version_id: str, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    await PolicyService.delete_version(db, ctx.campus_id, ctx.user_id, version_id)
    await db.commit()


@router.post("/versions/{version_id}/publish", response_model=PolicyVersionResponse)
async def publish_version(version_id: str, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    pv = await PolicyService.publish_version(db, ctx.campus_id, ctx.user_id, version_id)
    await db.commit()
    return pv


@router.post("/evaluations/dry-run", response_model=PolicyEvaluationResult)
async def dry_run(payload: DryRunRequest, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    """Evaluate flags against a policy without writing cases or evaluation rows."""
    flags = [f.model_copy(update={"campus_id": f.campus_id or ctx.campus_id}) for f in payload.flags]
    return await evaluate_risk_flags(
        db, ctx.campus_id, flags, ctx, dry_run=True, policy_version_id=payload.policy_version_id
    )


@router.get("/evaluations", response_model=List[EvaluationSummary])
async def list_evaluations(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db),
):
    return await PolicyService.list_evaluations(db, ctx.campus_id, limit, offset)


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str, ctx: TenancyContext = Depends(admin), db: AsyncSession = Depends(get_db)):
    ev, decisions = await PolicyService.get_evaluation(db, ctx.campus_id, evaluation_id)
    return {
        "evaluation": EvaluationSummary.model_validate(ev),
        "decisions": [DecisionResponse.model_validate(d) for d in decisions],
    }
