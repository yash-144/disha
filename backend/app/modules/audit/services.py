import uuid
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditEvent
from app.shared.utils import utc_now

GENESIS_HASH: str = "0" * 64

# Application-level per-campus concurrency locks to prevent forked chains
_campus_locks: Dict[str, asyncio.Lock] = {}
_locks_guard = asyncio.Lock()


async def get_campus_audit_lock(campus_id: str) -> asyncio.Lock:
    """Retrieve or initialize an asyncio.Lock specific to a campus."""
    async with _locks_guard:
        if campus_id not in _campus_locks:
            _campus_locks[campus_id] = asyncio.Lock()
        return _campus_locks[campus_id]


def format_audit_timestamp(dt: datetime) -> str:
    """Format datetime into consistent UTC ISO 8601 string across database backends."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()


def canonical_serialize(data: Any) -> str:
    """Deterministic canonical JSON serialization sorting all keys recursively."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def calculate_event_hash(
    prev_hash: str,
    campus_id: str,
    actor_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    event_metadata: Optional[Dict[str, Any]],
    created_at: datetime,
    correlation_id: Optional[str] = None,
) -> str:
    """
    Compute cryptographic SHA-256 hash over canonical representation of the audit event.
    hash = SHA-256(prev_hash || canonical_row) per DISHA Blueprint 07 §7 & AUD-01.
    """
    iso_time = format_audit_timestamp(created_at)
    canonical_payload = {
        "action": action,
        "actor_id": actor_id,
        "campus_id": campus_id,
        "correlation_id": correlation_id or "",
        "created_at": iso_time,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "metadata": event_metadata or {},
        "prev_hash": prev_hash,
    }
    serialized = canonical_serialize(canonical_payload)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuditService:
    """
    Authoritative Audit Service providing tamper-evident cryptographic hash chaining
    per campus tenancy conforming to DISHA Blueprint 07 §7 (AUD-01).
    """

    @staticmethod
    async def record_event(
        db: AsyncSession,
        actor_id: str,
        campus_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        event_metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditEvent:
        """
        Record an immutable audit event with sequential hash chaining.
        Guarantees serial chain progression even under concurrent requests or empty table.
        Does NOT commit, allowing the caller to control atomic transaction boundaries.
        """
        campus_lock = await get_campus_audit_lock(campus_id)
        async with campus_lock:
            # 1. In PostgreSQL, acquire transaction advisory lock to serialize across workers
            bind = getattr(db, "bind", None)
            dialect = getattr(bind, "dialect", None)
            if dialect and getattr(dialect, "name", "") == "postgresql":
                await db.execute(
                    text("SELECT pg_advisory_xact_lock(hashtext(:campus_id))"),
                    {"campus_id": campus_id},
                )

            # 2. Query the latest event for this campus to obtain previous event hash
            stmt = (
                select(AuditEvent)
                .where(AuditEvent.campus_id == campus_id)
                .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                .limit(1)
            )
            if dialect and getattr(dialect, "name", "") == "postgresql":
                stmt = stmt.with_for_update()

            res = await db.execute(stmt)
            latest_event = res.scalar_one_or_none()

            # 3. Previous hash resolution: Genesis if chain is empty, else latest event_hash
            prev_hash = (
                latest_event.event_hash
                if latest_event and latest_event.event_hash
                else GENESIS_HASH
            )

            # 4. Generate current event and calculate cryptographic hash
            now = utc_now()
            event_id = str(uuid.uuid4())
            curr_hash = calculate_event_hash(
                prev_hash=prev_hash,
                campus_id=campus_id,
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                event_metadata=event_metadata,
                created_at=now,
                correlation_id=correlation_id,
            )

            event = AuditEvent(
                id=event_id,
                actor_id=actor_id,
                campus_id=campus_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                event_metadata=event_metadata or {},
                correlation_id=correlation_id,
                prev_hash=prev_hash,
                event_hash=curr_hash,
                created_at=now,
            )
            db.add(event)
            await db.flush()
            return event

    @staticmethod
    async def verify_chain(
        db: AsyncSession,
        campus_id: str,
    ) -> Tuple[bool, Optional[str], int]:
        """
        Verify the cryptographic hash chain for a specific campus.
        Returns:
            (is_valid: bool, error_message: Optional[str], total_events: int)
        """
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.campus_id == campus_id)
            .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
        )
        res = await db.execute(stmt)
        events = res.scalars().all()

        if not events:
            return True, None, 0

        expected_prev = GENESIS_HASH
        for idx, ev in enumerate(events):
            # Check prev_hash linkage
            if ev.prev_hash != expected_prev:
                return (
                    False,
                    f"Chain linkage broken at index {idx} (event {ev.id}): expected prev_hash '{expected_prev}', found '{ev.prev_hash}'",
                    idx,
                )

            # Recompute and verify event_hash
            calculated = calculate_event_hash(
                prev_hash=ev.prev_hash,
                campus_id=ev.campus_id,
                actor_id=ev.actor_id,
                entity_type=ev.entity_type,
                entity_id=ev.entity_id,
                action=ev.action,
                event_metadata=ev.event_metadata,
                created_at=ev.created_at,
                correlation_id=ev.correlation_id,
            )
            if ev.event_hash != calculated:
                return (
                    False,
                    f"Tamper detected at index {idx} (event {ev.id}): stored event_hash '{ev.event_hash}' != recomputed '{calculated}'",
                    idx,
                )

            expected_prev = ev.event_hash

        return True, None, len(events)

    @staticmethod
    async def list_events(
        db: AsyncSession,
        campus_id: str,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """List audit events for a campus with optional entity filtering."""
        stmt = select(AuditEvent).where(AuditEvent.campus_id == campus_id)
        if entity_id:
            stmt = stmt.where(AuditEvent.entity_id == entity_id)
        if entity_type:
            stmt = stmt.where(AuditEvent.entity_type == entity_type)

        stmt = stmt.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit).offset(offset)
        res = await db.execute(stmt)
        return list(res.scalars().all())
