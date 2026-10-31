from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException, EntityNotFoundError, PermissionDeniedError
from app.modules.audit.services import AuditService
from app.modules.campus.models import Campus, MembershipInvite
from app.modules.campus.schemas import (
    ASSIGNABLE_ROLES,
    CampusCreateRequest,
    CampusDashboard,
    CampusSettings,
    CampusUpdateRequest,
    CounsellorWorkload,
    InviteCreateRequest,
    MembershipItem,
    MembershipUpdateRequest,
)
from app.modules.cases.models import Case
from app.modules.counselling.models import CounsellorProfile
from app.modules.identity.models import Membership, User
from app.modules.notifications.models import NotificationOutbox
from app.modules.roster.models import Student
from app.shared.enums import CaseState
from app.shared.utils import utc_now

TERMINAL = (CaseState.CLOSED.value, CaseState.DISMISSED.value)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CampusService:
    @staticmethod
    async def get(db: AsyncSession, campus_id: str) -> Campus:
        res = await db.execute(select(Campus).where(Campus.id == campus_id))
        campus = res.scalar_one_or_none()
        if not campus:
            raise EntityNotFoundError("Campus", campus_id)
        return campus

    @staticmethod
    async def load_settings(db: AsyncSession, campus_id: str) -> CampusSettings:
        """Settings for a campus, or the defaults when the campus has no settings row (used by the worker)."""
        raw = (await db.execute(select(Campus.settings).where(Campus.id == campus_id))).scalar_one_or_none()
        return CampusSettings.model_validate(raw or {})

    @staticmethod
    async def create(db: AsyncSession, actor_id: str, data: CampusCreateRequest) -> Campus:
        code = data.code.strip()
        dup = await db.execute(select(Campus.id).where(func.lower(Campus.code) == code.lower()))
        if dup.scalar_one_or_none():
            raise DishaBaseException("A campus with this code already exists", 409)
        settings = data.settings or CampusSettings()
        campus = Campus(name=data.name.strip(), code=code, settings=settings.model_dump(), created_by=actor_id)
        db.add(campus)
        await db.flush()
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus.id, entity_type="campus", entity_id=campus.id,
            action="CAMPUS_CREATED", event_metadata={"code": code},
        )
        return campus

    @staticmethod
    async def update(db: AsyncSession, campus_id: str, actor_id: str, data: CampusUpdateRequest) -> Campus:
        campus = await CampusService.get(db, campus_id)
        changed: List[str] = []
        if data.name is not None and data.name.strip() != campus.name:
            campus.name = data.name.strip()
            changed.append("name")
        if data.settings is not None:
            merged: Dict[str, Any] = dict(CampusSettings.model_validate(campus.settings or {}).model_dump())
            patch = data.settings.model_dump(exclude_unset=True)
            merged.update(patch)
            try:
                validated = CampusSettings.model_validate(merged)  # re-validate the whole document
            except ValidationError as exc:
                raise DishaBaseException(
                    "Invalid campus settings", 422, {"errors": [e["msg"] for e in exc.errors()]}
                )
            campus.settings = validated.model_dump()
            changed.extend(f"settings.{k}" for k in patch)
        campus.updated_at = utc_now()
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus_id, entity_type="campus", entity_id=campus_id,
            action="CAMPUS_UPDATED", event_metadata={"fields": changed},
        )
        await db.flush()
        return campus


def _item(m: Membership, u: User) -> MembershipItem:
    return MembershipItem(
        membership_id=m.id, user_id=u.id, email=u.email, full_name=u.full_name, role=m.role,
        department=m.department, is_active=m.is_active, user_is_active=u.is_active, created_at=m.created_at,
    )


class MembershipService:
    @staticmethod
    async def list(
        db: AsyncSession, campus_id: str, role: Optional[str], is_active: Optional[bool],
        search: Optional[str], limit: int, offset: int,
    ) -> List[MembershipItem]:
        stmt = select(Membership, User).join(User, User.id == Membership.user_id).where(
            Membership.campus_id == campus_id, Membership.role != "platform_admin"
        )
        if role:
            stmt = stmt.where(Membership.role == role)
        if is_active is not None:
            stmt = stmt.where(Membership.is_active == is_active)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(User.email).like(like) | func.lower(User.full_name).like(like))
        stmt = stmt.order_by(User.full_name).limit(limit).offset(offset)
        return [_item(m, u) for m, u in (await db.execute(stmt)).all()]

    @staticmethod
    async def update(
        db: AsyncSession, campus_id: str, actor_id: str, membership_id: str, data: MembershipUpdateRequest
    ) -> MembershipItem:
        res = await db.execute(
            select(Membership, User).join(User, User.id == Membership.user_id).where(
                Membership.id == membership_id, Membership.campus_id == campus_id
            )
        )
        pair = res.first()
        if not pair:
            raise EntityNotFoundError("Membership", membership_id)
        m, u = pair
        if m.user_id == actor_id:
            raise PermissionDeniedError("You cannot change your own membership")
        if m.role in ("platform_admin", "student"):
            raise PermissionDeniedError(f"Memberships with role '{m.role}' are not managed here")
        new_role = data.role.lower().strip() if data.role else m.role
        if new_role not in ASSIGNABLE_ROLES:
            raise DishaBaseException(f"Role '{new_role}' cannot be assigned", 422)
        new_active = m.is_active if data.is_active is None else data.is_active

        loses_admin = m.role == "institution_admin" and m.is_active and (new_role != m.role or not new_active)
        if loses_admin:
            others = (
                await db.execute(
                    select(func.count(Membership.id)).where(
                        Membership.campus_id == campus_id,
                        Membership.role == "institution_admin",
                        Membership.is_active == True,  # noqa: E712
                        Membership.id != m.id,
                    )
                )
            ).scalar_one()
            if others == 0:
                raise DishaBaseException("A campus must keep at least one active institution admin", 409)

        before = {"role": m.role, "department": m.department, "is_active": m.is_active}
        m.role = new_role
        if data.department is not None:
            m.department = data.department
        m.is_active = new_active
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus_id, entity_type="membership", entity_id=m.id,
            action="MEMBERSHIP_UPDATED",
            event_metadata={"before": before, "after": {"role": m.role, "department": m.department, "is_active": m.is_active}},
        )
        await db.flush()
        return _item(m, u)


def invite_status(inv: MembershipInvite, now: Optional[datetime] = None) -> str:
    now = now or utc_now()
    if inv.accepted_at:
        return "accepted"
    if inv.revoked_at:
        return "revoked"
    if _aware(inv.expires_at) < now:
        return "expired"
    return "pending"


class InviteService:
    """Invitations by email + role + campus. No credentials are created or sent: the invitee is linked on
    first Google sign-in, when the identity layer calls ``claim_for_email`` with the verified email."""

    @staticmethod
    async def create(db: AsyncSession, campus_id: str, actor_id: str, data: InviteCreateRequest) -> MembershipInvite:
        role = data.role.lower().strip()
        if role not in ASSIGNABLE_ROLES:
            raise DishaBaseException(f"Role '{role}' cannot be invited", 422)
        email = data.email.lower().strip()
        now = utc_now()

        member = await db.execute(
            select(Membership.id).join(User, User.id == Membership.user_id).where(
                func.lower(User.email) == email, Membership.campus_id == campus_id,
                Membership.role == role, Membership.is_active == True,  # noqa: E712
            )
        )
        if member.scalar_one_or_none():
            raise DishaBaseException("This person already has that role on the campus", 409)

        pending = await db.execute(
            select(MembershipInvite).where(
                MembershipInvite.campus_id == campus_id, MembershipInvite.email == email,
                MembershipInvite.role == role, MembershipInvite.accepted_at.is_(None),
                MembershipInvite.revoked_at.is_(None), MembershipInvite.expires_at > now,
            )
        )
        if pending.scalars().first():
            raise DishaBaseException("A pending invitation for this email and role already exists", 409)

        inv = MembershipInvite(
            campus_id=campus_id, email=email, role=role, department=data.department,
            expires_at=now + timedelta(days=data.expires_in_days), created_by=actor_id,
        )
        db.add(inv)
        await db.flush()
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus_id, entity_type="membership_invite", entity_id=inv.id,
            action="INVITE_CREATED", event_metadata={"role": role},
        )
        return inv

    @staticmethod
    async def list(db: AsyncSession, campus_id: str, status: Optional[str], limit: int, offset: int):
        stmt = select(MembershipInvite).where(MembershipInvite.campus_id == campus_id).order_by(
            MembershipInvite.created_at.desc()
        )
        invites = list((await db.execute(stmt)).scalars().all())
        if status:
            invites = [i for i in invites if invite_status(i) == status]
        return invites[offset: offset + limit]

    @staticmethod
    async def revoke(db: AsyncSession, campus_id: str, actor_id: str, invite_id: str) -> MembershipInvite:
        res = await db.execute(
            select(MembershipInvite).where(MembershipInvite.id == invite_id, MembershipInvite.campus_id == campus_id)
        )
        inv = res.scalar_one_or_none()
        if not inv:
            raise EntityNotFoundError("Invitation", invite_id)
        if invite_status(inv) != "pending":
            raise DishaBaseException(f"Only pending invitations can be revoked (this one is {invite_status(inv)})", 409)
        inv.revoked_at = utc_now()
        await AuditService.record_event(
            db, actor_id=actor_id, campus_id=campus_id, entity_type="membership_invite", entity_id=inv.id,
            action="INVITE_REVOKED", event_metadata={"role": inv.role},
        )
        await db.flush()
        return inv

    @staticmethod
    async def claim_for_email(db: AsyncSession, user_id: str, verified_email: str) -> List[Membership]:
        """Turn pending invitations for ``verified_email`` into memberships for ``user_id``.

        Call on sign-in after the identity provider has verified the email. Does not commit.
        """
        email = verified_email.lower().strip()
        now = utc_now()
        res = await db.execute(
            select(MembershipInvite).where(
                MembershipInvite.email == email, MembershipInvite.accepted_at.is_(None),
                MembershipInvite.revoked_at.is_(None), MembershipInvite.expires_at > now,
            )
        )
        created: List[Membership] = []
        for inv in res.scalars().all():
            existing = await db.execute(
                select(Membership).where(
                    Membership.user_id == user_id, Membership.campus_id == inv.campus_id, Membership.role == inv.role
                )
            )
            mem = existing.scalars().first()
            if mem is None:
                mem = Membership(
                    user_id=user_id, campus_id=inv.campus_id, role=inv.role, department=inv.department, is_active=True
                )
                db.add(mem)
                created.append(mem)
            elif not mem.is_active:
                mem.is_active = True
                created.append(mem)
            inv.accepted_at = now
            inv.accepted_by = user_id
            await db.flush()
            await AuditService.record_event(
                db, actor_id=user_id, campus_id=inv.campus_id, entity_type="membership_invite", entity_id=inv.id,
                action="INVITE_ACCEPTED", event_metadata={"role": inv.role, "membership_id": mem.id},
            )
        return created


class DashboardService:
    @staticmethod
    async def summary(db: AsyncSession, campus_id: str) -> CampusDashboard:
        now = utc_now()
        total_students = (
            await db.execute(
                select(func.count(Student.id)).where(Student.campus_id == campus_id, Student.is_active == True)  # noqa: E712
            )
        ).scalar_one()
        roles = (
            await db.execute(
                select(Membership.role, func.count(Membership.id))
                .where(Membership.campus_id == campus_id, Membership.is_active == True,  # noqa: E712
                       Membership.role.notin_(("student", "platform_admin")))
                .group_by(Membership.role)
            )
        ).all()

        cases = list(
            (await db.execute(select(Case).where(Case.campus_id == campus_id, Case.status.notin_(TERMINAL)))).scalars().all()
        )
        overdue = [c for c in cases if c.due_date and _aware(c.due_date) < now]
        escalated = [c for c in cases if c.escalated_deadline_version is not None
                     and c.escalated_deadline_version == c.deadline_version]

        counsellors = (
            await db.execute(
                select(User.id, User.full_name).join(Membership, Membership.user_id == User.id).where(
                    Membership.campus_id == campus_id, Membership.role == "counsellor", Membership.is_active == True  # noqa: E712
                )
            )
        ).all()
        profiles = {
            p.user_id: p.availability_status
            for p in (await db.execute(select(CounsellorProfile).where(CounsellorProfile.campus_id == campus_id))).scalars()
        }
        workload = [
            CounsellorWorkload(
                user_id=uid, full_name=name,
                active_cases=sum(1 for c in cases if c.assigned_counsellor_id == uid),
                overdue_cases=sum(1 for c in overdue if c.assigned_counsellor_id == uid),
                availability_status=profiles.get(uid),
            )
            for uid, name in counsellors
        ]
        pending_invites = (
            await db.execute(
                select(func.count(MembershipInvite.id)).where(
                    MembershipInvite.campus_id == campus_id, MembershipInvite.accepted_at.is_(None),
                    MembershipInvite.revoked_at.is_(None), MembershipInvite.expires_at > now,
                )
            )
        ).scalar_one()
        dead = (
            await db.execute(
                select(func.count(NotificationOutbox.id)).where(
                    NotificationOutbox.campus_id == campus_id, NotificationOutbox.status == "dead_letter"
                )
            )
        ).scalar_one()
        return CampusDashboard(
            total_students=total_students, staff_by_role={r: n for r, n in roles}, active_cases=len(cases),
            overdue_cases=len(overdue), escalated_cases=len(escalated), pending_invites=pending_invites,
            dead_letter_notifications=dead, counsellor_workload=workload,
        )
