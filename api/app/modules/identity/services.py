from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.modules.identity.models import User, Membership
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from typing import Optional, List, Dict, Any
import uuid


class IdentityService:

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.id == user_id, User.is_active == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(
            select(User).where(User.email == email.lower().strip(), User.is_active == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_memberships(db: AsyncSession, user_id: str) -> List[Membership]:
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.is_active == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_membership(
        db: AsyncSession, user_id: str, campus_id: str
    ) -> Optional[Membership]:
        result = await db.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.campus_id == campus_id,
                Membership.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: str,
        user_id: Optional[str] = None,
    ) -> User:
        hashed = get_password_hash(password)
        user = User(
            id=user_id or str(uuid.uuid4()),
            email=email.lower().strip(),
            hashed_password=hashed,
            full_name=full_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def add_membership(
        db: AsyncSession,
        user_id: str,
        campus_id: str,
        role: str,
        department: Optional[str] = None,
        membership_id: Optional[str] = None,
    ) -> Membership:
        membership = Membership(
            id=membership_id or str(uuid.uuid4()),
            user_id=user_id,
            campus_id=campus_id,
            role=role.lower().strip(),
            department=department,
            is_active=True,
        )
        db.add(membership)
        await db.flush()
        return membership

    @staticmethod
    async def login(
        db: AsyncSession, email: str, password: str
    ) -> Dict[str, Any]:
        user = await IdentityService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        memberships = await IdentityService.get_active_memberships(db, user.id)
        membership_dicts = [
            {
                "id": m.id,
                "campus_id": m.campus_id,
                "role": m.role,
                "department": m.department,
                "is_active": m.is_active,
            }
            for m in memberships
        ]

        token_data = {
            "sub": user.id,
            "email": user.email,
            "roles": [m.role for m in memberships],
            "memberships": membership_dicts,
            "is_platform_admin": any(m.role == "platform_admin" for m in memberships),
        }
        token = create_access_token(data=token_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "memberships": membership_dicts,
        }

    @staticmethod
    async def google_login(
        db: AsyncSession,
        email: str,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        campus_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        email_clean = email.lower().strip()
        user = await IdentityService.get_user_by_email(db, email_clean)
        if not user:
            name = full_name or email_clean.split("@")[0].replace(".", " ").title()
            user = await IdentityService.create_user(
                db=db,
                email=email_clean,
                password=str(uuid.uuid4()),
                full_name=name,
            )
            c_id = campus_id or "campus-1"
            r_val = role or "counsellor"
            await IdentityService.add_membership(
                db=db,
                user_id=user.id,
                campus_id=c_id,
                role=r_val,
                department="General",
            )
            await db.commit()

        # Claim any pending invitations for verified Google email
        try:
            from app.modules.campus.services import MembershipInviteService
            claimed = await MembershipInviteService.claim_for_email(db, user.id, email_clean)
            if claimed:
                await db.commit()
        except Exception:
            pass

        memberships = await IdentityService.get_active_memberships(db, user.id)
        if not memberships and role:
            c_id = campus_id or "campus-1"
            m = await IdentityService.add_membership(
                db=db,
                user_id=user.id,
                campus_id=c_id,
                role=role,
                department="General",
            )
            await db.commit()
            memberships = [m]

        # If student membership exists, ensure roster entry is present
        if any(m.role == "student" for m in memberships):
            try:
                from app.modules.roster.models import Student
                c_id = campus_id or (memberships[0].campus_id if memberships else "campus-1")
                s_stmt = select(Student).where(Student.user_id == user.id, Student.campus_id == c_id)
                s_res = await db.execute(s_stmt)
                student_rec = s_res.scalar_one_or_none()
                if not student_rec:
                    s_email_stmt = select(Student).where(Student.email == email_clean, Student.campus_id == c_id)
                    s_res = await db.execute(s_email_stmt)
                    student_rec = s_res.scalar_one_or_none()
                    if student_rec and not student_rec.user_id:
                        student_rec.user_id = user.id
                        await db.commit()
                if not student_rec:
                    student_rec = Student(
                        campus_id=c_id,
                        user_id=user.id,
                        student_uid=f"STU-{user.id[:8].upper()}",
                        full_name=user.full_name,
                        email=email_clean,
                        department="Computer Science",
                        course="B.Tech",
                        academic_year=2026,
                        cohort_code="COHORT-2026",
                        enrollment_status="active",
                        attendance_rate=92.5,
                        quiz_score_avg=84.0,
                        is_active=True,
                    )
                    db.add(student_rec)
                    await db.commit()
            except Exception:
                pass

        membership_dicts = [
            {
                "id": m.id,
                "campus_id": m.campus_id,
                "role": m.role,
                "department": m.department,
                "is_active": m.is_active,
            }
            for m in memberships
        ]

        token_data = {
            "sub": user.id,
            "email": user.email,
            "roles": [m.role for m in memberships],
            "memberships": membership_dicts,
            "is_platform_admin": any(m.role == "platform_admin" for m in memberships),
        }
        token = create_access_token(data=token_data)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "memberships": membership_dicts,
        }
