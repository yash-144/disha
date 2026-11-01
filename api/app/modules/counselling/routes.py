from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.modules.counselling.permissions import (
    ASSIGNMENT_ROLES,
    CASELOAD_VIEW_ROLES,
    COUNSELLOR_ROLES,
    SESSION_VIEW_ROLES,
    SESSION_WRITE_ROLES,
)
from app.modules.counselling.schemas import (
    AssignmentCreate,
    AssignmentOut,
    CaseloadItem,
    CounsellorDashboard,
    NoteCreate,
    NoteOut,
    ProfileOut,
    ProfileUpsert,
    SessionCancel,
    SessionCreate,
    SessionOut,
    SessionReschedule,
    StudentItem,
)
from app.modules.counselling.services import (
    AssignmentService,
    CaseloadService,
    NoteService,
    ProfileService,
    SessionService,
)
from app.modules.interventions.schemas import FollowUpOut
from app.shared.idempotency import verify_idempotency_key
from app.shared.idempotency_store import run_idempotent

router = APIRouter(tags=["Counselling"])

require_counsellor = require_role(*COUNSELLOR_ROLES)
require_caseload_view = require_role(*CASELOAD_VIEW_ROLES)
require_session_write = require_role(*SESSION_WRITE_ROLES)
require_session_view = require_role(*SESSION_VIEW_ROLES)
require_assignment_admin = require_role(*ASSIGNMENT_ROLES)


# ----------------------------------------------------------------- dashboard / caseload
@router.get("/dashboard", response_model=CounsellorDashboard)
async def counsellor_dashboard(ctx: TenancyContext = Depends(require_counsellor), db: AsyncSession = Depends(get_db)):
    return await CaseloadService.dashboard(db, ctx)


@router.get("/caseload", response_model=List[CaseloadItem])
async def caseload(
    counsellor_id: Optional[str] = Query(None, description="Supervisors only"),
    state: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    include_closed: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_caseload_view),
    db: AsyncSession = Depends(get_db),
):
    """Cases owned by the counsellor (their own), or by a named counsellor for HOD / admins."""
    return await CaseloadService.list_cases(db, ctx, counsellor_id, state, overdue_only, include_closed, limit, offset)


@router.get("/students", response_model=List[StudentItem])
async def caseload_students(
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_counsellor),
    db: AsyncSession = Depends(get_db),
):
    return await CaseloadService.list_students(db, ctx, q, limit, offset)


@router.get("/followups", response_model=List[FollowUpOut])
async def my_followups(
    upcoming_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_caseload_view),
    db: AsyncSession = Depends(get_db),
):
    return await CaseloadService.list_followups(db, ctx, upcoming_only, limit, offset)


# ----------------------------------------------------------------------- profile
@router.get("/profile", response_model=ProfileOut)
async def get_profile(ctx: TenancyContext = Depends(require_counsellor), db: AsyncSession = Depends(get_db)):
    return ProfileOut.model_validate(await ProfileService.get(db, ctx))


@router.put("/profile", response_model=ProfileOut)
async def upsert_profile(
    payload: ProfileUpsert, ctx: TenancyContext = Depends(require_counsellor), db: AsyncSession = Depends(get_db)
):
    """Create or update the caller's own profile. Role and campus come from the membership, not the body."""
    p = await ProfileService.upsert(db, ctx, payload)
    await db.commit()
    return ProfileOut.model_validate(p)


# ---------------------------------------------------------------------- sessions
@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_session_write),
    db: AsyncSession = Depends(get_db),
):
    async def produce():
        return await SessionService.create(db, ctx, payload)

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope="session.create", body=payload.model_dump(), produce=produce,
    )


@router.get("/sessions", response_model=List[SessionOut])
async def list_sessions(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(scheduled|completed|cancelled|no_show)$"),
    from_: Optional[datetime] = Query(None, alias="from"),
    to: Optional[datetime] = Query(None),
    student_id: Optional[str] = Query(None),
    counsellor_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_session_view),
    db: AsyncSession = Depends(get_db),
):
    return await SessionService.list(db, ctx, status_filter, from_, to, student_id, counsellor_id, limit, offset)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str = Path(...), ctx: TenancyContext = Depends(require_session_view), db: AsyncSession = Depends(get_db)
):
    return await SessionService.get(db, ctx, session_id)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def reschedule_session(
    payload: SessionReschedule,
    session_id: str = Path(...),
    ctx: TenancyContext = Depends(require_session_write),
    db: AsyncSession = Depends(get_db),
):
    out = await SessionService.reschedule(db, ctx, session_id, payload)
    await db.commit()
    return out


@router.post("/sessions/{session_id}/cancel", response_model=SessionOut)
async def cancel_session(
    payload: SessionCancel,
    session_id: str = Path(...),
    ctx: TenancyContext = Depends(require_session_write),
    db: AsyncSession = Depends(get_db),
):
    out = await SessionService.cancel(db, ctx, session_id, payload)
    await db.commit()
    return out


@router.post("/sessions/{session_id}/complete", response_model=SessionOut)
async def complete_session(
    session_id: str = Path(...), ctx: TenancyContext = Depends(require_session_write), db: AsyncSession = Depends(get_db)
):
    out = await SessionService.complete(db, ctx, session_id)
    await db.commit()
    return out


@router.post("/sessions/{session_id}/no-show", response_model=SessionOut)
async def session_no_show(
    session_id: str = Path(...), ctx: TenancyContext = Depends(require_session_write), db: AsyncSession = Depends(get_db)
):
    out = await SessionService.no_show(db, ctx, session_id)
    await db.commit()
    return out


# ------------------------------------------------------------ confidential notes
@router.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_counsellor),
    db: AsyncSession = Depends(get_db),
):
    """Confidential counselling note. Append-only; counsellors in scope only (not admins)."""
    async def produce():
        return NoteOut.model_validate(await NoteService.create(db, ctx, payload))

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope="counselling.note", body=payload.model_dump(), produce=produce,
    )


@router.get("/students/{student_id}/notes", response_model=List[NoteOut])
async def list_student_notes(
    student_id: str = Path(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_counsellor),
    db: AsyncSession = Depends(get_db),
):
    rows = await NoteService.list_for_student(db, ctx, student_id, limit, offset)
    await db.commit()  # persists the read-access audit event
    return [NoteOut.model_validate(r) for r in rows]


# ------------------------------------------------------------------- assignments
@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    payload: AssignmentCreate,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_assignment_admin),
    db: AsyncSession = Depends(get_db),
):
    async def produce():
        return AssignmentOut.model_validate(await AssignmentService.create(db, ctx, payload))

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope="counselling.assignment", body=payload.model_dump(), produce=produce,
    )


@router.get("/assignments", response_model=List[AssignmentOut])
async def list_assignments(
    counsellor_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_assignment_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = await AssignmentService.list(db, ctx, counsellor_id, student_id, active_only, limit, offset)
    return [AssignmentOut.model_validate(r) for r in rows]


@router.delete("/assignments/{assignment_id}", response_model=AssignmentOut)
async def end_assignment(
    assignment_id: str = Path(...),
    ctx: TenancyContext = Depends(require_assignment_admin),
    db: AsyncSession = Depends(get_db),
):
    a = await AssignmentService.end(db, ctx, assignment_id)
    await db.commit()
    return AssignmentOut.model_validate(a)
