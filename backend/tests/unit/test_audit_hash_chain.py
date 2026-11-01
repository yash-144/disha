"""
DISHA Authoritative Audit Hash Chain Verification Tests (AUD-01 & Blueprint 07 §7)

Verifies:
1. First event in a campus chain receives GENESIS_HASH ("0"*64) as prev_hash.
2. Sequential previous-hash linkage across multiple events in a campus.
3. Cryptographic hash verification and tamper detection when an event is corrupted.
4. Independent hash chains per campus (campus-level isolation).
5. Concurrency safety: parallel audit writes for the same campus maintain chain integrity.
6. Case transaction rollback if audit recording fails.
7. Verification that all CaseService operations (create, update, transition) produce valid hash-chained events.
"""

import unittest
import asyncio
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import patch

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.shared.enums import CaseState, CaseStatus
from app.shared.utils import utc_now
from app.core.permissions import Role
from app.modules.identity.models import User
from app.modules.roster.models import Student
from app.modules.cases.models import Case, CaseEvent
from app.modules.audit.models import AuditEvent
from app.modules.audit.services import (
    AuditService,
    GENESIS_HASH,
    calculate_event_hash,
    canonical_serialize,
)
from app.modules.cases.schemas import (
    CaseCreateRequest,
    CaseUpdateRequest,
)
from app.modules.cases.services import CaseService


class TestAuditHashChain(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.campus_a = "campus-ipp-01"
        self.campus_b = "campus-ipp-02"

        self.student_id = str(uuid.uuid4())
        self.counsellor_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())

        async with self.async_session() as session:
            async with session.begin():
                s = Student(
                    id=self.student_id,
                    campus_id=self.campus_a,
                    student_uid="STU-001",
                    full_name="Ananya Roy",
                    department="Computer Science",
                    course="B.Tech",
                    academic_year=2,
                    is_active=True,
                )
                counsellor = User(
                    id=self.counsellor_id,
                    email="priya@disha.edu",
                    hashed_password="fake",
                    full_name="Priya Nair",
                    is_active=True,
                )
                admin = User(
                    id=self.admin_id,
                    email="admin@disha.edu",
                    hashed_password="fake",
                    full_name="Admin User",
                    is_active=True,
                )
                session.add_all([s, counsellor, admin])

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_first_event_in_campus_chain(self):
        """Verify first event for a campus receives GENESIS_HASH and valid event_hash."""
        async with self.async_session() as session:
            async with session.begin():
                ev = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="CASE_CREATED",
                    event_metadata={"title": "First Case"},
                )

            self.assertEqual(ev.prev_hash, GENESIS_HASH)
            self.assertIsNotNone(ev.event_hash)
            self.assertEqual(len(ev.event_hash), 64)

            # Recompute expected hash
            expected = calculate_event_hash(
                prev_hash=GENESIS_HASH,
                campus_id=self.campus_a,
                actor_id=self.admin_id,
                entity_type="case",
                entity_id="case-1001",
                action="CASE_CREATED",
                event_metadata={"title": "First Case"},
                created_at=ev.created_at,
            )
            self.assertEqual(ev.event_hash, expected)

    async def test_sequential_hash_linkage(self):
        """Verify sequential events link previous_hash to preceding event_hash."""
        async with self.async_session() as session:
            async with session.begin():
                ev1 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="EVENT_1",
                    event_metadata={"step": 1},
                )
            async with session.begin():
                ev2 = await AuditService.record_event(
                    db=session,
                    actor_id=self.counsellor_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="EVENT_2",
                    event_metadata={"step": 2},
                )
            async with session.begin():
                ev3 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="EVENT_3",
                    event_metadata={"step": 3},
                )

            self.assertEqual(ev1.prev_hash, GENESIS_HASH)
            self.assertEqual(ev2.prev_hash, ev1.event_hash)
            self.assertEqual(ev3.prev_hash, ev2.event_hash)

            # Verify complete chain
            is_valid, err, count = await AuditService.verify_chain(session, self.campus_a)
            self.assertTrue(is_valid)
            self.assertIsNone(err)
            self.assertEqual(count, 3)

    async def test_hash_verification_and_tamper_detection(self):
        """Verify that altering an event's data or prev_hash breaks chain verification."""
        async with self.async_session() as session:
            async with session.begin():
                await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="INIT",
                    event_metadata={"status": "initial"},
                )
            async with session.begin():
                target_ev = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-1001",
                    action="UPDATE",
                    event_metadata={"status": "updated"},
                )

            # Prior to tamper: valid
            is_valid, err, count = await AuditService.verify_chain(session, self.campus_a)
            self.assertTrue(is_valid)

            # Tamper 1: modify metadata without recalculating hash
            await session.execute(
                update(AuditEvent)
                .where(AuditEvent.id == target_ev.id)
                .values(event_metadata={"status": "TAMPERED_BY_MALICIOUS_ACTOR"})
            )
            await session.commit()

            is_valid, err, idx = await AuditService.verify_chain(session, self.campus_a)
            self.assertFalse(is_valid)
            self.assertIn("Tamper detected", err)
            self.assertEqual(idx, 1)

    async def test_independent_chains_for_different_campuses(self):
        """Verify independent hash chains per campus (isolation)."""
        async with self.async_session() as session:
            # Record 2 events in Campus A
            async with session.begin():
                a1 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-A",
                    action="ACTION_A1",
                )
            async with session.begin():
                a2 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_a,
                    entity_type="case",
                    entity_id="case-A",
                    action="ACTION_A2",
                )

            # Record 2 events in Campus B
            async with session.begin():
                b1 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_b,
                    entity_type="case",
                    entity_id="case-B",
                    action="ACTION_B1",
                )
            async with session.begin():
                b2 = await AuditService.record_event(
                    db=session,
                    actor_id=self.admin_id,
                    campus_id=self.campus_b,
                    entity_type="case",
                    entity_id="case-B",
                    action="ACTION_B2",
                )

            # Both campus genesis events have GENESIS_HASH
            self.assertEqual(a1.prev_hash, GENESIS_HASH)
            self.assertEqual(b1.prev_hash, GENESIS_HASH)

            # Campus A links internally
            self.assertEqual(a2.prev_hash, a1.event_hash)

            # Campus B links internally
            self.assertEqual(b2.prev_hash, b1.event_hash)

            # Hashes do not collide across campuses
            self.assertNotEqual(a1.event_hash, b1.event_hash)

            # Verify each campus chain independently
            valid_a, _, count_a = await AuditService.verify_chain(session, self.campus_a)
            valid_b, _, count_b = await AuditService.verify_chain(session, self.campus_b)
            self.assertTrue(valid_a)
            self.assertTrue(valid_b)
            self.assertEqual(count_a, 2)
            self.assertEqual(count_b, 2)

    async def test_concurrent_writes_and_chain_integrity(self):
        """Verify parallel audit writes for the same campus produce a contiguous, unforked chain."""
        num_concurrent = 8

        async def worker(index: int):
            async with self.async_session() as session:
                async with session.begin():
                    return await AuditService.record_event(
                        db=session,
                        actor_id=self.admin_id,
                        campus_id=self.campus_a,
                        entity_type="case",
                        entity_id="concurrent-case",
                        action=f"PARALLEL_ACTION_{index}",
                        event_metadata={"index": index},
                    )

        # Fire parallel write tasks simultaneously
        tasks = [worker(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        self.assertEqual(len(results), num_concurrent)

        # Verify the resulting chain is strictly unbroken
        async with self.async_session() as session:
            is_valid, err, count = await AuditService.verify_chain(session, self.campus_a)
            self.assertTrue(is_valid, f"Chain validation failed: {err}")
            self.assertEqual(count, num_concurrent)

    async def test_case_transaction_rollback_if_audit_fails(self):
        """Verify full transaction rollback if AuditService.record_event raises an exception."""
        case_id = None
        async with self.async_session() as session:
            case = await CaseService.create_case(
                db=session,
                campus_id=self.campus_a,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_id,
                    title="Audit Failure Test",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )
            case_id = case.id
            self.assertEqual(case.version, 1)

            # Simulate AuditService.record_event failure
            with patch("app.modules.cases.services.AuditService.record_event", side_effect=RuntimeError("Audit hardware HSM failure")):
                with self.assertRaises(RuntimeError):
                    await CaseService.transition_case_db(
                        db=session,
                        case_id=case_id,
                        campus_id=self.campus_a,
                        actor_user_id=self.admin_id,
                        actor_roles=[Role.INSTITUTION_ADMIN.value],
                        target_state_raw=CaseState.ASSIGNED.value,
                        expected_version=1,
                        new_owner_id=self.counsellor_id,
                        due_at=utc_now() + timedelta(days=2),
                    )

        # In a fresh session, confirm rollback: status remains ACTION_PLANNED, version remains 1
        async with self.async_session() as fresh_session:
            fresh = await CaseService.get_case(fresh_session, case_id, self.campus_a)
            self.assertEqual(fresh.status, CaseState.ACTION_PLANNED.value)
            self.assertEqual(fresh.version, 1)

            # Confirm no second audit event was persisted
            audits = await fresh_session.scalars(
                select(AuditEvent).where(AuditEvent.entity_id == case_id)
            )
            self.assertEqual(len(audits.all()), 1)

    async def test_all_caseservice_operations_use_auditservice(self):
        """Verify create, update, and transition all produce valid hash-chained audit events."""
        async with self.async_session() as session:
            # 1. Create case
            c = await CaseService.create_case(
                db=session,
                campus_id=self.campus_a,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseCreateRequest(
                    student_id=self.student_id,
                    title="Full Audit Pipeline Case",
                    initial_state=CaseState.ACTION_PLANNED.value,
                ),
            )

            # 2. Update case
            await CaseService.update_case(
                db=session,
                case_id=c.id,
                campus_id=self.campus_a,
                actor_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                data=CaseUpdateRequest(
                    expected_version=1,
                    title="Updated Title For Audit",
                ),
            )

            # 3. Transition case
            await CaseService.transition_case_db(
                db=session,
                case_id=c.id,
                campus_id=self.campus_a,
                actor_user_id=self.admin_id,
                actor_roles=[Role.INSTITUTION_ADMIN.value],
                target_state_raw=CaseState.ASSIGNED.value,
                expected_version=2,
                new_owner_id=self.counsellor_id,
                due_at=utc_now() + timedelta(days=3),
            )

            # Query all audit events for this campus
            stmt = select(AuditEvent).where(AuditEvent.campus_id == self.campus_a).order_by(AuditEvent.created_at.asc())
            events = (await session.scalars(stmt)).all()
            self.assertEqual(len(events), 3)

            # Every event MUST have non-null prev_hash and event_hash
            for ev in events:
                self.assertIsNotNone(ev.prev_hash)
                self.assertIsNotNone(ev.event_hash)
                self.assertEqual(len(ev.prev_hash), 64)
                self.assertEqual(len(ev.event_hash), 64)

            # Verify the entire chain is cryptographically valid
            is_valid, err, count = await AuditService.verify_chain(session, self.campus_a)
            self.assertTrue(is_valid, f"Verification failed: {err}")
            self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
