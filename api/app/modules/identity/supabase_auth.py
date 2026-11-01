"""Verification of Supabase-issued access tokens (Google sign-in) before a DISHA token is minted."""
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings

_jwks_client: Optional[PyJWKClient] = None


def _unauthorised(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


async def verify_supabase_token(authorization: Optional[str]) -> Dict[str, Any]:
    """Return the verified claims of a Supabase access token; raises 401 otherwise. Requires a verified email."""
    global _jwks_client
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorised("Supabase access token required")
    token = authorization.split(" ", 1)[1].strip()
    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
        if alg == "HS256":
            if not settings.SUPABASE_JWT_SECRET:
                raise _unauthorised("Server is not configured to verify HS256 Supabase tokens")
            claims = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        else:
            if _jwks_client is None:
                _jwks_client = PyJWKClient(f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json")
            key = _jwks_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(token, key, algorithms=[alg], audience="authenticated")
    except HTTPException:
        raise
    except Exception:
        raise _unauthorised("Invalid or expired Supabase token")
    if not claims.get("email"):
        raise _unauthorised("Token carries no email")
    return claims
