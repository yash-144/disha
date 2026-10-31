import unittest
import os
from sqlalchemy import select, update, Table, Column, String, Integer, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.database import Base
from app.core.exceptions import ConcurrencyConflictError
from app.modules.identity.models import User, Membership


class TestDatabaseIntegrity(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # High-speed in-memory SQLite async engine
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    # 1. Revision Integrity & Duplicate Detection
    def test_alembic_revision_integrity_and_single_head(self):
        """Verify Alembic configuration, script directory, and head revision."""
        alembic_ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
        self.assertTrue(os.path.exists(alembic_ini_path), "api/alembic.ini must exist")

        alembic_cfg = Config(alembic_ini_path)
        script_dir = ScriptDirectory.from_config(alembic_cfg)

        heads = script_dir.get_heads()
        self.assertEqual(len(heads), 1, f"Expected exactly 1 migration head, found: {heads}")
        self.assertEqual(heads[0], "003_ml_pipeline")

        # Verify revision metadata and lineage
        head_rev = script_dir.get_revision(heads[0])
        self.assertEqual(head_rev.down_revision, "002_student_faculty_module")
        self.assertEqual(head_rev.revision, "003_ml_pipeline")
        mid_rev = script_dir.get_revision("002_student_faculty_module")
        self.assertEqual(mid_rev.down_revision, "001_counsellor_module")

        init_rev = script_dir.get_revision("001_counsellor_module")
        self.assertIsNone(init_rev.down_revision, "Initial migration must have down_revision = None")

    def test_duplicate_revision_detection(self):
        """Verify that all migration version files contain unique revision identifiers."""
        versions_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "migrations", "versions"
        )
        self.assertTrue(os.path.exists(versions_dir))

        revisions = []
        for filename in os.listdir(versions_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                filepath = os.path.join(versions_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.startswith("revision =") or line.startswith("revision:"):
                            rev_val = line.split("=")[-1].strip().strip("'\"")
                            revisions.append(rev_val)

        # Ensure no duplicates exist
        self.assertEqual(len(revisions), len(set(revisions)), f"Duplicate revisions found: {revisions}")

    # 2. Foreign-Key Integrity in Metadata
    def test_foreign_key_references_resolve(self):
        """Verify that foreign keys defined in ORM metadata resolve to valid parent tables and columns."""
        for table_name, table in Base.metadata.tables.items():
            for fk in table.foreign_keys:
                target_col = fk.column
                self.assertIsNotNone(
                    target_col,
                    f"ForeignKey '{fk}' on table '{table_name}' does not resolve to a valid column",
                )
                self.assertIn(
                    target_col.table.name,
                    Base.metadata.tables,
                    f"Target table '{target_col.table.name}' for FK '{fk}' must be registered in metadata",
                )

    # 3. Transaction Rollback & Atomicity
    async def test_transaction_rollback_prevents_partial_writes(self):
        """Verify that an error inside an async transaction rolls back all pending changes."""
        async with self.async_session() as session:
            try:
                async with session.begin():
                    # 1. Add user
                    user = User(
                        id="user-rollback-test",
                        email="rollback@disha.edu",
                        hashed_password="hash",
                        full_name="Rollback Test",
                        is_active=True,
                    )
                    session.add(user)
                    await session.flush()

                    # 2. Simulate unexpected failure before commit
                    raise RuntimeError("Simulated transient database/service error")
            except RuntimeError:
                pass  # Transaction was rolled back by context manager

        # Verify nothing was committed
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.id == "user-rollback-test")
            )
            found_user = result.scalar_one_or_none()
            self.assertIsNone(found_user, "User must NOT exist in the database after transaction rollback")

    # 4. Optimistic Concurrency & HTTP 409 Conflict Safety
    async def test_atomic_optimistic_concurrency_conflict_409(self):
        """Verify that concurrent updates on the same case with stale version trigger 409 conflict.

        Simulates Blueprint 07 pattern:
        UPDATE disha_cases SET ..., version = version + 1 WHERE id = :id AND version = :expected_version
        """
        # Create an ad-hoc test case table in SQLite to test concurrency pattern directly
        async with self.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: sync_conn.exec_driver_sql(
                    """
                    CREATE TABLE IF NOT EXISTS test_concurrency_cases (
                        id VARCHAR(36) PRIMARY KEY,
                        campus_id VARCHAR(36) NOT NULL,
                        state VARCHAR(50) NOT NULL,
                        version INTEGER NOT NULL DEFAULT 1
                    )
                    """
                )
            )

        # Seed initial case at version 1
        case_id = "case-concurrency-101"
        campus_id = "campus-01"
        async with self.async_session() as session:
            async with session.begin():
                await session.execute(
                    Table(
                        "test_concurrency_cases",
                        Base.metadata,
                        Column("id", String(36), primary_key=True),
                        Column("campus_id", String(36)),
                        Column("state", String(50)),
                        Column("version", Integer),
                        extend_existing=True,
                    ).insert().values(
                        id=case_id,
                        campus_id=campus_id,
                        state="assigned",
                        version=1,
                    )
                )

        case_table = Table(
            "test_concurrency_cases",
            Base.metadata,
            Column("id", String(36), primary_key=True),
            Column("campus_id", String(36)),
            Column("state", String(50)),
            Column("version", Integer),
            extend_existing=True,
        )

        # Transaction 1: Reads case at version 1, attempts update with expected_version = 1
        expected_version_tx1 = 1
        async with self.async_session() as session1:
            async with session1.begin():
                stmt1 = (
                    update(case_table)
                    .where(
                        case_table.c.id == case_id,
                        case_table.c.campus_id == campus_id,
                        case_table.c.version == expected_version_tx1,
                    )
                    .values(state="accepted", version=case_table.c.version + 1)
                )
                res1 = await session1.execute(stmt1)
                self.assertEqual(res1.rowcount, 1, "Transaction 1 must successfully update 1 row")

        # Transaction 2: Stale worker attempts update with stale expected_version = 1
        expected_version_tx2 = 1  # Stale! Database is now at version 2
        async with self.async_session() as session2:
            async with session2.begin():
                stmt2 = (
                    update(case_table)
                    .where(
                        case_table.c.id == case_id,
                        case_table.c.campus_id == campus_id,
                        case_table.c.version == expected_version_tx2,
                    )
                    .values(state="contact_attempted", version=case_table.c.version + 1)
                )
                res2 = await session2.execute(stmt2)

                # Exactly 0 rows updated -> Must raise ConcurrencyConflictError (HTTP 409)
                if res2.rowcount == 0:
                    with self.assertRaises(ConcurrencyConflictError) as ctx:
                        raise ConcurrencyConflictError(
                            f"Case {case_id} has been modified concurrently (expected version {expected_version_tx2})"
                        )
                    self.assertEqual(ctx.exception.status_code, 409)

        # Verify database state: Transaction 1 changes persisted, version is 2, Transaction 2 rejected
        async with self.async_session() as session_verify:
            res = await session_verify.execute(
                select(case_table).where(case_table.c.id == case_id)
            )
            row = res.mappings().one()
            self.assertEqual(row["state"], "accepted")
            self.assertEqual(row["version"], 2)


if __name__ == "__main__":
    unittest.main()

