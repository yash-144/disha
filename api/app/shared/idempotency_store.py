"""Stored-response idempotency for POST endpoints (blueprint 05 section 1).

Same key and same body returns the stored response; same key and a different body
is a 409 ``IDEMPOTENCY_KEY_REUSED``. The record is written in the same transaction
as the work it protects, so a failed request leaves no record behind.

The header itself is validated by ``app.shared.idempotency.verify_idempotency_key``.
"""
import hashlib
import json
import uuid
from typing import Any, Awaitable, Callable, Dict

from fastapi.encoders import jsonable_encoder
from sqlalchemy import JSON, Column, DateTime, Integer, String, UniqueConstraint, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.core.exceptions import DishaBaseException
from app.shared.utils import utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")


class IdempotencyRecord(Base):
    __tablename__ = "disha_idempotency_keys"
    __table_args__ = (UniqueConstraint("campus_id", "actor_id", "key", name="uq_idempotency_campus_actor_key"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campus_id = Column(String(36), nullable=False, index=True)
    actor_id = Column(String(36), nullable=False)
    key = Column(String(200), nullable=False)
    scope = Column(String(100), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_status = Column(Integer, nullable=False, default=200)
    response_body = Column(JSONType, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


def _hash(scope: str, body: Any) -> str:
    canonical = json.dumps(jsonable_encoder(body), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{scope}|{canonical}".encode()).hexdigest()


async def _lookup(db: AsyncSession, campus_id: str, actor_id: str, key: str):
    res = await db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.campus_id == campus_id,
            IdempotencyRecord.actor_id == actor_id,
            IdempotencyRecord.key == key,
        )
    )
    return res.scalar_one_or_none()


def _replay(rec: IdempotencyRecord, request_hash: str) -> Dict[str, Any]:
    if rec.request_hash != request_hash:
        raise DishaBaseException(
            "Idempotency-Key was already used with a different request body",
            409,
            {"code": "IDEMPOTENCY_KEY_REUSED"},
        )
    return rec.response_body


async def run_idempotent(
    db: AsyncSession,
    *,
    campus_id: str,
    actor_id: str,
    key: str,
    scope: str,
    body: Any,
    produce: Callable[[], Awaitable[Any]],
) -> Dict[str, Any]:
    """Run ``produce`` once per (campus, actor, key); commit the work and the record together.

    ``produce`` must flush but not commit, and return something JSON-encodable.
    """
    request_hash = _hash(scope, body)
    existing = await _lookup(db, campus_id, actor_id, key)
    if existing:
        return _replay(existing, request_hash)

    result = jsonable_encoder(await produce())
    db.add(
        IdempotencyRecord(
            campus_id=campus_id,
            actor_id=actor_id,
            key=key,
            scope=scope,
            request_hash=request_hash,
            response_status=200,
            response_body=result,
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        # a concurrent request with the same key won; discard our work and replay its response
        await db.rollback()
        existing = await _lookup(db, campus_id, actor_id, key)
        if existing:
            return _replay(existing, request_hash)
        raise
    return result
