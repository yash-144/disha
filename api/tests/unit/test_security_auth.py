import unittest
from datetime import timedelta
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.core.dependencies import get_current_user


class TestSecurityAuth(unittest.IsolatedAsyncioTestCase):

    def test_password_hashing_and_verification(self):
        password = "SecureDISHA#Password2026"
        hashed = get_password_hash(password)

        # Ensure Argon2id scheme is applied
        self.assertTrue(hashed.startswith("$argon2id$") or hashed.startswith("$bcrypt$"))

        # Verify matching password
        self.assertTrue(verify_password(password, hashed))

        # Verify incorrect password fails
        self.assertFalse(verify_password("WrongPassword123", hashed))

        # Verify empty password fails safely
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(password, ""))

    def test_token_creation_and_decoding(self):
        user_data = {
            "sub": "user-uuid-123",
            "email": "counsellor@disha.edu",
            "roles": ["counsellor"],
            "campus_id": "campus-01",
        }
        token = create_access_token(user_data, expires_delta=timedelta(minutes=15))
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

        payload = decode_access_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user-uuid-123")
        self.assertEqual(payload["email"], "counsellor@disha.edu")
        self.assertEqual(payload["roles"], ["counsellor"])
        self.assertEqual(payload["campus_id"], "campus-01")
        self.assertIn("exp", payload)

    def test_token_expiration(self):
        user_data = {"sub": "user-expired-999"}
        # Issue token that already expired 5 seconds ago
        expired_token = create_access_token(user_data, expires_delta=timedelta(seconds=-5))

        payload = decode_access_token(expired_token)
        self.assertIsNone(payload, "Expired token must decode to None")

    def test_token_signature_tampering(self):
        user_data = {"sub": "user-tamper-001", "role": "student"}
        valid_token = create_access_token(user_data, expires_delta=timedelta(minutes=30))

        parts = valid_token.split(".")
        # Tamper signature part by mutating the last character
        tampered_sig = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

        self.assertIsNone(decode_access_token(tampered_token), "Tampered signature must return None")

    def test_malformed_token_rejection(self):
        malformed_cases = [
            "",
            "not-a-token",
            "header.payload",
            "header.payload.sig.extra",
            "invalid_base64.invalid_payload.invalid_sig",
            None,
        ]
        for token in malformed_cases:
            with self.subTest(token=token):
                self.assertIsNone(decode_access_token(token), f"Token '{token}' must be rejected")

    async def test_get_current_user_valid_token(self):
        user_data = {"sub": "user-valid-555", "email": "valid@disha.edu"}
        token = create_access_token(user_data)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        payload = await get_current_user(credentials)
        self.assertEqual(payload["sub"], "user-valid-555")
        self.assertEqual(payload["email"], "valid@disha.edu")

    async def test_get_current_user_missing_credentials(self):
        with self.assertRaises(HTTPException) as ctx:
            await get_current_user(None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("WWW-Authenticate", ctx.exception.headers)

    async def test_get_current_user_expired_token_raises_401(self):
        token = create_access_token({"sub": "user-1"}, expires_delta=timedelta(seconds=-10))
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        with self.assertRaises(HTTPException) as ctx:
            await get_current_user(credentials)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid or expired token", ctx.exception.detail)

    async def test_get_current_user_tampered_token_raises_401(self):
        token = create_access_token({"sub": "user-1"})
        tampered = token[:-4] + "zzzz"
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tampered)

        with self.assertRaises(HTTPException) as ctx:
            await get_current_user(credentials)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid or expired token", ctx.exception.detail)

    async def test_get_current_user_malformed_token_raises_401(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token.here")

        with self.assertRaises(HTTPException) as ctx:
            await get_current_user(credentials)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid or expired token", ctx.exception.detail)

    def test_fastapi_endpoint_authentication_flow(self):
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        test_app = FastAPI()

        @test_app.get("/protected")
        def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"authenticated_user": user["sub"]}

        client = TestClient(test_app)

        # 1. Valid Token -> 200 OK
        valid_tok = create_access_token({"sub": "disha-counsellor-01"})
        res_valid = client.get("/protected", headers={"Authorization": f"Bearer {valid_tok}"})
        self.assertEqual(res_valid.status_code, 200)
        self.assertEqual(res_valid.json(), {"authenticated_user": "disha-counsellor-01"})

        # 2. Missing Token -> 401 Unauthorized
        res_missing = client.get("/protected")
        self.assertEqual(res_missing.status_code, 401)

        # 3. Expired Token -> 401 Unauthorized
        exp_tok = create_access_token({"sub": "expired-user"}, expires_delta=timedelta(seconds=-1))
        res_expired = client.get("/protected", headers={"Authorization": f"Bearer {exp_tok}"})
        self.assertEqual(res_expired.status_code, 401)

        # 4. Tampered Signature -> 401 Unauthorized
        tampered_tok = valid_tok[:-6] + "xxxxxx"
        res_tampered = client.get("/protected", headers={"Authorization": f"Bearer {tampered_tok}"})
        self.assertEqual(res_tampered.status_code, 401)

    async def test_google_login_service(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from app.core.database import Base
        from app.modules.identity.services import IdentityService
        from app.modules.campus.models import Campus  # noqa: F401  (table must exist for the default campus lookup)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            # 1. New Google user -> student membership (roles are never taken from the client)
            res1 = await IdentityService.google_login(
                db,
                email="prof.sharma@iitb.ac.in",
                full_name="Prof. Sharma",
            )
            self.assertIn("access_token", res1)
            self.assertEqual(res1["email"], "prof.sharma@iitb.ac.in")
            self.assertEqual(res1["full_name"], "Prof. Sharma")
            self.assertEqual(res1["memberships"][0]["role"], "student")

            # Verify token
            decoded = decode_access_token(res1["access_token"])
            self.assertIsNotNone(decoded)
            self.assertEqual(decoded["sub"], res1["user_id"])
            self.assertIn("student", decoded["roles"])

            # 2. Existing Google User Login -> retrieves existing user
            res2 = await IdentityService.google_login(
                db,
                email="prof.sharma@iitb.ac.in",
                full_name="Prof. Sharma",
            )
            self.assertEqual(res2["user_id"], res1["user_id"])
            self.assertEqual(res2["email"], "prof.sharma@iitb.ac.in")

        await engine.dispose()


if __name__ == "__main__":
    unittest.main()
