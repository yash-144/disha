"""Campus administration: settings, memberships and role assignment, invitations, dashboard.

Invitations carry no credentials. People sign in with Google; the identity layer links a pending
invitation to the user on first sign-in (``InviteService.claim_for_email``).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, get_tenancy_context, require_role
from app.core.permissions import Role
from app.modules.campus.permissions import ADMIN_ROLES, SETTINGS_READ_ROLES
from app.modules.campus.schemas import (
    CampusCreateRequest,
    CampusDashboard,
    CampusResponse,
    CampusSettings,
    CampusUpdateRequest,
    InviteCreateRequest,
    InviteResponse,
    MembershipItem,
    MembershipUpdateRequest,
)
from app.modules.campus.services import (
    CampusService,
    DashboardService,
    InviteService,
    MembershipService,
    invite_status,
)
from app.shared.idempotency import verify_idempotency_key
from app.shared.idempotency_store import run_idempotent

router = APIRouter(tags=["Campus"])

require_admin = require_role(*ADMIN_ROLES)
require_platform_admin = require_role(Role.PLATFORM_ADMIN)


def _campus_out(c) -> CampusResponse:
    return CampusResponse(
        id=c.id, name=c.name, code=c.code, is_active=c.is_active,
        settings=CampusSettings.model_validate(c.settings or {}),
        created_at=c.created_at, updated_at=c.updated_at,
    )


def _invite_out(i) -> InviteResponse:
    return InviteResponse(
        id=i.id, campus_id=i.campus_id, email=i.email, role=i.role, department=i.department,
        status=invite_status(i), expires_at=i.expires_at, created_by=i.created_by,
        created_at=i.created_at, accepted_at=i.accepted_at,
    )


@router.get("", response_model=CampusResponse)
async def get_campus(ctx: TenancyContext = Depends(get_tenancy_context), db: AsyncSession = Depends(get_db)):
    """The active campus (any member)."""
    return _campus_out(await CampusService.get(db, ctx.campus_id))


@router.post("", response_model=CampusResponse, status_code=status.HTTP_201_CREATED)
async def create_campus(
    payload: CampusCreateRequest,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a campus (platform admin only)."""
    async def produce():
        return _campus_out(await CampusService.create(db, ctx.user_id, payload))

    return await run_idempotent(
        db, campus_id="platform", actor_id=ctx.user_id, key=idempotency_key,
        scope="campus.create", body=payload.model_dump(), produce=produce,
    )


@router.get("/settings", response_model=CampusSettings)
async def get_settings(
    ctx: TenancyContext = Depends(require_role(*SETTINGS_READ_ROLES)), db: AsyncSession = Depends(get_db)
):
    return CampusSettings.model_validate((await CampusService.get(db, ctx.campus_id)).settings or {})


@router.patch("", response_model=CampusResponse)
async def update_campus(
    payload: CampusUpdateRequest,
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the campus name and settings (escalation levels, channels, follow-up grace)."""
    campus = await CampusService.update(db, ctx.campus_id, ctx.user_id, payload)
    await db.commit()
    return _campus_out(campus)


@router.get("/dashboard", response_model=CampusDashboard)
async def dashboard(ctx: TenancyContext = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await DashboardService.summary(db, ctx.campus_id)


@router.get("/memberships", response_model=List[MembershipItem])
async def list_memberships(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await MembershipService.list(db, ctx.campus_id, role, is_active, q, limit, offset)


@router.patch("/memberships/{membership_id}", response_model=MembershipItem)
async def update_membership(
    payload: MembershipUpdateRequest,
    membership_id: str = Path(...),
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a member's role, department or active flag. Role assignment lives here only."""
    item = await MembershipService.update(db, ctx.campus_id, ctx.user_id, membership_id, payload)
    await db.commit()
    return item


@router.post("/invitations", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    payload: InviteCreateRequest,
    idempotency_key: str = Depends(verify_idempotency_key),
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Invite an email address to the campus with a role. They are linked on first Google sign-in."""
    async def produce():
        return _invite_out(await InviteService.create(db, ctx.campus_id, ctx.user_id, payload))

    return await run_idempotent(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, key=idempotency_key,
        scope="campus.invite", body=payload.model_dump(), produce=produce,
    )


@router.get("/invitations", response_model=List[InviteResponse])
async def list_invitations(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(pending|accepted|revoked|expired)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return [_invite_out(i) for i in await InviteService.list(db, ctx.campus_id, status_filter, limit, offset)]


@router.delete("/invitations/{invitation_id}", response_model=InviteResponse)
async def revoke_invitation(
    invitation_id: str = Path(...),
    ctx: TenancyContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    inv = await InviteService.revoke(db, ctx.campus_id, ctx.user_id, invitation_id)
    await db.commit()
    return _invite_out(inv)
