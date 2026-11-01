from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenancy_context, TenancyContext
from app.core.permissions import Role
from app.modules.audit.services import AuditService
from app.modules.audit.schemas import AuditVerificationResponse, AuditEventDetailResponse

router = APIRouter(tags=["Audit"])


@router.get("/verify", response_model=AuditVerificationResponse)
async def verify_audit_chain(
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify cryptographic hash-chain integrity for the tenant campus (Blueprint 07 §7 / AUD-01).
    Restricted to institution admins and platform admins.
    """
    if ctx.role not in (Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN) and not ctx.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators may verify the audit hash chain.",
        )

    is_valid, error, total = await AuditService.verify_chain(db, ctx.campus_id)
    return AuditVerificationResponse(
        campus_id=ctx.campus_id,
        is_valid=is_valid,
        total_events=total,
        error=error,
    )


@router.get("", response_model=List[AuditEventDetailResponse])
@router.get("/", response_model=List[AuditEventDetailResponse])
async def list_audit_events(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    ctx: TenancyContext = Depends(get_tenancy_context),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve campus-scoped audit trail events. Administrators only."""
    if ctx.role not in (Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN) and not ctx.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators may read the audit trail.")
    events = await AuditService.list_events(
        db=db,
        campus_id=ctx.campus_id,
        entity_id=entity_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )
    return events
