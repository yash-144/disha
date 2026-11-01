"""Case access helpers shared by the counselling and interventions modules.

Cases are always looked up inside the caller's active campus: a case in another campus is a 404,
even for platform admins (NFR-TEN-03).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TenancyContext
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.core.permissions import Role
from app.modules.cases.models import Case
from app.shared.enums import CaseState, map_status_to_state

TERMINAL_STATES = (CaseState.CLOSED.value, CaseState.DISMISSED.value)

# roles that may act on a case they own; hod and platform admin supervise any case in the campus
OWNER_ROLES = {Role.COUNSELLOR, Role.FACULTY, Role.MENTOR}
SUPERVISOR_ROLES = {Role.HOD, Role.PLATFORM_ADMIN}


def aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def load_case(db: AsyncSession, campus_id: str, case_id: str) -> Case:
    res = await db.execute(select(Case).where(Case.id == case_id, Case.campus_id == campus_id))
    case = res.scalar_one_or_none()
    if not case:
        raise EntityNotFoundError("Case", case_id)
    return case


def assert_case_writer(ctx: TenancyContext, case: Case) -> None:
    """The case owner, an HOD, or a platform admin may change a case's interventions and follow-ups.

    Institution admins supervise but do not modify active counselling work (verify_resource_access rule).
    """
    if ctx.role in SUPERVISOR_ROLES or ctx.is_platform_admin:
        return
    if ctx.role in OWNER_ROLES and case.assigned_counsellor_id == ctx.user_id:
        return
    raise PermissionDeniedError("Only the assigned owner of this case (or an HOD) may modify it")


def assert_case_open(case: Case) -> None:
    from app.core.exceptions import StateTransitionError

    state = map_status_to_state(case.status).value
    if state in TERMINAL_STATES:
        raise StateTransitionError(state, state, "The case is closed or dismissed; reopen it first")
