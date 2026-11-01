from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, get_tenancy_context, require_role
from app.core.permissions import Role
from app.modules.notifications.schemas import NotificationItem, NotificationPage, OutboxItem, UnreadCount
from app.modules.notifications.services import InboxService, OutboxAdminService

router = APIRouter(tags=["Notifications"])

# Dead-letter visibility and retry belong to institution admins (OUT-06).
require_outbox_admin = require_role(Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN)


@router.get("", response_model=NotificationPage)
@router.get("/", response_model=NotificationPage, include_in_schema=False)
async def list_my_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """The caller's own in-app notifications in the active campus, newest first."""
    rows, next_cursor = await InboxService.list_for_user(db, ctx.campus_id, ctx.user_id, unread_only, limit, cursor, role=ctx.role.value)
    return NotificationPage(items=[NotificationItem.model_validate(r) for r in rows], next_cursor=next_cursor)


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(ctx: TenancyContext = Depends(get_tenancy_context), db: AsyncSession = Depends(get_db)):
    return UnreadCount(unread=await InboxService.unread_count(db, ctx.campus_id, ctx.user_id, role=ctx.role.value))


@router.post("/read-all", response_model=UnreadCount)
async def mark_all_read(ctx: TenancyContext = Depends(get_tenancy_context), db: AsyncSession = Depends(get_db)):
    await InboxService.mark_all_read(db, ctx.campus_id, ctx.user_id, role=ctx.role.value)
    await db.commit()
    return UnreadCount(unread=0)


@router.get("/outbox", response_model=List[OutboxItem])
async def list_outbox(
    status: Optional[str] = Query(None, pattern="^(pending|sent|failed|dead_letter)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: TenancyContext = Depends(require_outbox_admin),
    db: AsyncSession = Depends(get_db),
):
    rows = await OutboxAdminService.list_outbox(db, ctx.campus_id, status, limit, offset)
    return [OutboxItem.model_validate(r) for r in rows]


@router.post("/outbox/{outbox_id}/retry", response_model=OutboxItem)
async def retry_outbox_item(
    outbox_id: str = Path(...),
    ctx: TenancyContext = Depends(require_outbox_admin),
    db: AsyncSession = Depends(get_db),
):
    row = await OutboxAdminService.retry(db, ctx.campus_id, ctx.user_id, outbox_id)
    await db.commit()
    return OutboxItem.model_validate(row)


@router.patch("/{notification_id}/read", response_model=NotificationItem)
async def mark_read(
    notification_id: str = Path(...),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    notif = await InboxService.mark_read(db, ctx.campus_id, ctx.user_id, notification_id)
    await db.commit()
    return NotificationItem.model_validate(notif)
