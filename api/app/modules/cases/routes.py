from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenancy_context, TenancyContext
from app.core.meko import get_meko
from app.core.permissions import Role
from app.modules.meko.hooks import schedule_case_decision
from app.modules.cases.schemas import (
    CaseCreateRequest,
    CaseUpdateRequest,
    CaseAssignRequest,
    CaseReopenRequest,
    CaseDismissRequest,
    CaseTransitionRequest,
    CaseDetailResponse,
    CaseEventResponse,
)
from app.modules.cases.services import CaseService, CaseLifecycleService, case_to_detail_response
from app.shared.enums import CaseState, CaseStatus, map_status_to_state, map_state_to_status

router = APIRouter(tags=["Cases"])


def _extract_actor_context(current_user: dict, ctx: TenancyContext):
    actor_id = ctx.user_id
    roles = [ctx.role.value]
    if "roles" in current_user and isinstance(current_user["roles"], list):
        roles.extend(current_user["roles"])
    if ctx.is_platform_admin and "platform_admin" not in roles:
        roles.append("platform_admin")
    return actor_id, list(set(roles))


@router.post("", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreateRequest,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Create a new case in the persistent database with strict campus isolation."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    case = await CaseService.create_case(
        db=db,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        data=payload,
    )
    await db.commit()
    return case_to_detail_response(case)


@router.get("", response_model=List[CaseDetailResponse])
@router.get("/", response_model=List[CaseDetailResponse])
async def list_cases(
    state: Optional[str] = Query(None, description="Filter by canonical CaseState"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by legacy CaseStatus or CaseState"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    assigned_counsellor_id: Optional[str] = Query(None, description="Filter by assigned counsellor ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """List cases with strict campus-level tenancy boundary and optional filtering."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    cases = await CaseService.list_cases(
        db=db,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        is_platform_admin=ctx.is_platform_admin,
        state=state,
        status_filter=status_filter,
        priority=priority,
        student_id=student_id,
        assigned_counsellor_id=assigned_counsellor_id,
        limit=limit,
        offset=offset,
    )
    return [case_to_detail_response(c) for c in cases]


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: str = Path(...),
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve case details with canonical state and legacy status compatibility from database."""
    case = await CaseService.get_case(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        is_platform_admin=ctx.is_platform_admin,
    )
    return case_to_detail_response(case)


@router.patch("/{case_id}", response_model=CaseDetailResponse)
async def update_case(
    case_id: str = Path(...),
    payload: CaseUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Update case metadata using atomic database-level optimistic locking."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    updated_case = await CaseService.update_case(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        data=payload,
        is_platform_admin=ctx.is_platform_admin,
    )
    await db.commit()
    return case_to_detail_response(updated_case)


@router.post("/{case_id}/transition")
async def transition_case_state(
    case_id: str = Path(...),
    payload: CaseTransitionRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
    tasks: BackgroundTasks = BackgroundTasks(),
    meko=Depends(get_meko),
):
    """
    Execute canonical state transition governed by the 14-state transition matrix
    with atomic database concurrency, tenancy isolation, and transactional audit logging.
    """
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    result = await CaseService.transition_case_db(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        actor_user_id=actor_id,
        actor_roles=actor_roles,
        target_state_raw=payload.target_state,
        expected_version=payload.expected_version,
        reason_code=payload.reason_code,
        notes=payload.notes,
        new_owner_id=payload.new_owner_id,
        due_at=payload.due_at,
        # guard facts are read from the database; client flags are not trusted
        has_follow_up=False,
        has_outcome=False,
        is_platform_admin=ctx.is_platform_admin,
    )

    await db.commit()
    accepted = payload.target_state == "under_review" and result["event"]["from_state"] == "suggested"
    if accepted or payload.target_state == "dismissed":
        await schedule_case_decision(tasks, meko, db, case_id=case_id, action="accept" if accepted else "dismiss",
                                     role=ctx.role.value, campus_id=ctx.campus_id, note=payload.reason_code)
    return {
        "status": "success",
        "case": result["case"],
        "event": result["event"],
        "notification_intent": result["notification_intent"],
    }


@router.post("/{case_id}/assign", response_model=CaseDetailResponse)
async def assign_case(
    case_id: str = Path(...),
    payload: CaseAssignRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Assign or reassign a case to a counsellor."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    case = await CaseService.assign_case(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        data=payload,
        is_platform_admin=ctx.is_platform_admin,
    )
    await db.commit()
    return case_to_detail_response(case)


@router.post("/{case_id}/reopen", response_model=CaseDetailResponse)
async def reopen_case(
    case_id: str = Path(...),
    payload: CaseReopenRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Formally reopen a closed case."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    case = await CaseService.reopen_case(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        data=payload,
        is_platform_admin=ctx.is_platform_admin,
    )
    await db.commit()
    return case_to_detail_response(case)


@router.post("/{case_id}/dismiss", response_model=CaseDetailResponse)
async def dismiss_case(
    case_id: str = Path(...),
    payload: CaseDismissRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
    tasks: BackgroundTasks = BackgroundTasks(),
    meko=Depends(get_meko),
):
    """Dismiss a case early with mandatory rationale."""
    actor_id, actor_roles = _extract_actor_context(current_user, ctx)
    case = await CaseService.dismiss_case(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        actor_id=actor_id,
        actor_roles=actor_roles,
        data=payload,
        is_platform_admin=ctx.is_platform_admin,
    )
    await db.commit()
    await schedule_case_decision(tasks, meko, db, case_id=case_id, action="dismiss", role=ctx.role.value,
                                 campus_id=ctx.campus_id, note=payload.reason_code)
    return case_to_detail_response(case)


@router.get("/{case_id}/events", response_model=List[CaseEventResponse])
async def get_case_events(
    case_id: str = Path(...),
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve audit timeline of lifecycle events for a case."""
    return await CaseService.get_case_events(
        db=db,
        case_id=case_id,
        campus_id=ctx.campus_id,
        is_platform_admin=ctx.is_platform_admin,
    )


@router.post("/{case_id}/accept")
async def accept_case(
    case_id: str = Path(...),
    payload: CaseTransitionRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Convenience endpoint to accept an assigned case."""
    payload.target_state = CaseState.ACCEPTED.value
    return await transition_case_state(
        case_id=case_id,
        payload=payload,
        current_user=current_user,
        ctx=ctx,
        db=db,
    )


@router.post("/{case_id}/close")
async def close_case(
    case_id: str = Path(...),
    payload: CaseTransitionRequest = ...,
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Convenience endpoint to close a case upon resolution."""
    payload.target_state = CaseState.CLOSED.value
    return await transition_case_state(
        case_id=case_id,
        payload=payload,
        current_user=current_user,
        ctx=ctx,
        db=db,
    )
