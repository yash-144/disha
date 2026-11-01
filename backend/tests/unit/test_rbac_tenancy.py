import unittest
import asyncio
from datetime import timedelta
from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.core.permissions import Role, Action
from app.core.dependencies import (
    get_current_user,
    get_tenancy_context,
    require_role,
    require_permission,
    verify_resource_access,
    TenancyContext,
)
from app.modules.identity.models import User, Membership
from app.modules.identity.services import IdentityService


class TestRBACTenancy(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # In-memory SQLite async engine for high-speed, isolated testing
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed test users and memberships
        async with self.async_session() as session:
            # 1. Platform Admin
            self.platform_admin = await IdentityService.create_user(
                session, "superadmin@disha.gov", "AdminPass@2026", "Global Administrator", "user-platform-admin"
            )
            await IdentityService.add_membership(
                session, self.platform_admin.id, "campus-platform", Role.PLATFORM_ADMIN.value
            )

            # 2. Institution Admin (Campus A)
            self.inst_admin = await IdentityService.create_user(
                session, "admin.ipp@institution.edu", "AdminPass@2026", "Campus Director", "user-inst-admin"
            )
            await IdentityService.add_membership(
                session, self.inst_admin.id, "campus-ipp-01", Role.INSTITUTION_ADMIN.value
            )

            # 3. Counsellor 1 (Campus A)
            self.counsellor_1 = await IdentityService.create_user(
                session, "elena.counsellor@institution.edu", "CounsellorPass@2026", "Dr. Elena Rostova", "user-counsellor-01"
            )
            await IdentityService.add_membership(
                session, self.counsellor_1.id, "campus-ipp-01", Role.COUNSELLOR.value, "Guidance"
            )

            # 4. Counsellor 2 (Campus A)
            self.counsellor_2 = await IdentityService.create_user(
                session, "marcus.counsellor@institution.edu", "CounsellorPass@2026", "Dr. Marcus Vance", "user-counsellor-02"
            )
            await IdentityService.add_membership(
                session, self.counsellor_2.id, "campus-ipp-01", Role.COUNSELLOR.value, "Guidance"
            )

            # 5. Faculty Member (Campus A)
            self.faculty = await IdentityService.create_user(
                session, "faculty.john@institution.edu", "FacultyPass@2026", "Prof. Johnathan Myers", "user-faculty-01"
            )
            await IdentityService.add_membership(
                session, self.faculty.id, "campus-ipp-01", Role.FACULTY.value, "Informatics"
            )

            # 6. Student (Campus A)
            self.student = await IdentityService.create_user(
                session, "student.ana@institution.edu", "StudentPass@2026", "Ana Silva", "user-student-01"
            )
            await IdentityService.add_membership(
                session, self.student.id, "campus-ipp-01", Role.STUDENT.value, "Engineering"
            )

            # 7. Deactivated User
            self.deactivated_user = await IdentityService.create_user(
                session, "deactivated@institution.edu", "DeactPass@2026", "Deactivated User", "user-deact-01"
            )
            self.deactivated_user.is_active = False

            # 8. User with deactivated membership
            self.revoked_user = await IdentityService.create_user(
                session, "revoked@institution.edu", "RevokedPass@2026", "Revoked Membership User", "user-revoked-01"
            )
            revoked_membership = await IdentityService.add_membership(
                session, self.revoked_user.id, "campus-ipp-01", Role.COUNSELLOR.value
            )
            revoked_membership.is_active = False

            await session.commit()

        # Build test FastAPI application
        self.app = FastAPI()

        async def override_get_db():
            async with self.async_session() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db

        # Define protected test routes mapping to each permission & role tier
        @self.app.get("/platform/config")
        def platform_config_route(tenancy: TenancyContext = Depends(require_permission(Action.MANAGE_PLATFORM_CONFIG))):
            return {"status": "ok", "user": tenancy.email, "role": tenancy.role.value}

        @self.app.get("/admin/users")
        def admin_users_route(tenancy: TenancyContext = Depends(require_permission(Action.MANAGE_CAMPUS_USERS))):
            return {"status": "ok", "campus": tenancy.campus_id, "role": tenancy.role.value}

        @self.app.get("/counselling/confidential-notes")
        def confidential_notes_route(tenancy: TenancyContext = Depends(require_permission(Action.VIEW_CONFIDENTIAL_NOTES))):
            return {"status": "ok", "notes": "Protected Clinical Reflection", "counsellor": tenancy.user_id}

        @self.app.put("/cases/{case_id}")
        def update_case_route(
            case_id: str,
            assigned_counsellor_id: str = "user-counsellor-01",
            case_campus_id: str = "campus-ipp-01",
            tenancy: TenancyContext = Depends(require_permission(Action.UPDATE_ASSIGNED_CASES)),
        ):
            verify_resource_access(
                tenancy=tenancy,
                resource_campus_id=case_campus_id,
                assigned_counsellor_id=assigned_counsellor_id,
                for_update=True,
            )
            return {"status": "updated", "case_id": case_id}

        @self.app.get("/cases/{case_id}/confidential-note")
        def get_case_confidential_note(
            case_id: str,
            assigned_counsellor_id: str = "user-counsellor-01",
            case_campus_id: str = "campus-ipp-01",
            tenancy: TenancyContext = Depends(require_permission(Action.VIEW_CONFIDENTIAL_NOTES)),
        ):
            verify_resource_access(
                tenancy=tenancy,
                resource_campus_id=case_campus_id,
                assigned_counsellor_id=assigned_counsellor_id,
                is_confidential=True,
            )
            return {"status": "ok", "case_id": case_id, "content": "Sensitive counselling content"}

        self.client = TestClient(self.app)

    async def asyncTearDown(self):
        await self.engine.dispose()

    def _token_headers(self, user_id: str, email: str, campus_id: str = "campus-ipp-01") -> dict:
        token = create_access_token({"sub": user_id, "email": email, "campus_id": campus_id})
        return {"Authorization": f"Bearer {token}", "X-Campus-ID": campus_id}

    # 1. Unauthenticated requests
    def test_unauthenticated_request_rejected(self):
        res = self.client.get("/admin/users")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication token required", res.json()["detail"])

    # 2. Student accessing Admin endpoints -> 403 Forbidden
    def test_student_accessing_admin_endpoints_forbidden(self):
        headers = self._token_headers(self.student.id, self.student.email)
        res = self.client.get("/admin/users", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    # 3. Faculty accessing Counsellor endpoints -> 403 Forbidden
    def test_faculty_accessing_counsellor_endpoints_forbidden(self):
        headers = self._token_headers(self.faculty.id, self.faculty.email)
        res = self.client.get("/counselling/confidential-notes", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    # 4. Counsellor accessing Admin endpoints -> 403 Forbidden
    def test_counsellor_accessing_admin_endpoints_forbidden(self):
        headers = self._token_headers(self.counsellor_1.id, self.counsellor_1.email)
        res = self.client.get("/admin/users", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("does not have permission", res.json()["detail"])

    # 5. Institution Admin accessing another campus -> 403 Forbidden
    def test_institution_admin_accessing_another_campus_forbidden(self):
        # Admin is registered only for 'campus-ipp-01', attempts to access 'campus-other-99'
        token = create_access_token({"sub": self.inst_admin.id, "email": self.inst_admin.email})
        headers = {"Authorization": f"Bearer {token}", "X-Campus-ID": "campus-other-99"}
        res = self.client.get("/admin/users", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("No active membership found for campus 'campus-other-99'", res.json()["detail"])

    # 6. Counsellor accessing another counsellor's assigned case -> 403 Forbidden
    def test_counsellor_accessing_another_counsellors_case_forbidden(self):
        # Case is assigned to counsellor 1, but counsellor 2 attempts to update or view confidential note
        headers_c2 = self._token_headers(self.counsellor_2.id, self.counsellor_2.email)
        res_update = self.client.put("/cases/case-101", headers=headers_c2)
        self.assertEqual(res_update.status_code, 403)
        self.assertIn("Only the assigned counsellor may modify this case", res_update.json()["detail"])

        res_note = self.client.get("/cases/case-101/confidential-note", headers=headers_c2)
        self.assertEqual(res_note.status_code, 403)
        self.assertIn("Counsellor is not assigned to this confidential record", res_note.json()["detail"])

        # Assigned counsellor (counsellor 1) accesses case -> 200 OK
        headers_c1 = self._token_headers(self.counsellor_1.id, self.counsellor_1.email)
        res_ok_update = self.client.put("/cases/case-101", headers=headers_c1)
        self.assertEqual(res_ok_update.status_code, 200)

        res_ok_note = self.client.get("/cases/case-101/confidential-note", headers=headers_c1)
        self.assertEqual(res_ok_note.status_code, 200)

    # 7. Deactivated membership -> 403 Forbidden
    def test_deactivated_membership_forbidden(self):
        headers = self._token_headers(self.revoked_user.id, self.revoked_user.email)
        res = self.client.get("/counselling/confidential-notes", headers=headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("No active membership found", res.json()["detail"])

    # 8. Deactivated user account -> 401 Unauthorized
    def test_deactivated_user_rejected(self):
        headers = self._token_headers(self.deactivated_user.id, self.deactivated_user.email)
        res = self.client.get("/counselling/confidential-notes", headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn("deactivated", res.json()["detail"])

    # 9. Platform Admin global permissions -> 200 OK
    def test_platform_admin_permissions_allowed(self):
        headers = {
            "Authorization": f"Bearer {create_access_token({'sub': self.platform_admin.id, 'email': self.platform_admin.email})}",
            "X-Campus-ID": "campus-ipp-01",
        }
        res_platform = self.client.get("/platform/config", headers=headers)
        self.assertEqual(res_platform.status_code, 200)

        res_campus_users = self.client.get("/admin/users", headers=headers)
        self.assertEqual(res_campus_users.status_code, 200)

    # 10. Confidential counselling note access: Admin strictly blocked
    def test_admin_cannot_access_confidential_counselling_notes(self):
        headers_admin = self._token_headers(self.inst_admin.id, self.inst_admin.email)
        res = self.client.get("/counselling/confidential-notes", headers=headers_admin)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Institution Admins do not have access to confidential counselling notes", res.json()["detail"])

    # 11. Cross-campus data isolation
    def test_cross_campus_data_isolation_returns_404(self):
        headers_c1 = self._token_headers(self.counsellor_1.id, self.counsellor_1.email, "campus-ipp-01")
        # Attempting to access case belonging to 'campus-other-99'
        res = self.client.put("/cases/case-cross?case_campus_id=campus-other-99", headers=headers_c1)
        self.assertEqual(res.status_code, 404)
        self.assertIn("Resource not found in the active campus", res.json()["detail"])


if __name__ == "__main__":
    unittest.main()

