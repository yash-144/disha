"""Worker jobs against a SQLite database: outbox dispatch and deadline escalation end to end."""
import asyncio
import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # worker/ so `scheduler` imports
pytest.importorskip("aiosqlite")
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from worker.jobs import _db, deadline_escalation, outbox_dispatch  # also puts api/ on sys.path
from app.core.database import Base
import app.modules.cases.models as m
from app.modules.cases.services import CasesService
from app.shared.utils import utc_now


@pytest.fixture
def sm(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/w.db", poolclass=NullPool)

    async def create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create())
    maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(_db, "session", maker)
    yield maker
    asyncio.run(engine.dispose())


def test_escalation_job_escalates_overdue_case_once(sm):
    async def seed():
        async with sm() as db:
            c = await CasesService(db).create_from_flag("c1", "u1", "f1", "S1")
            await CasesService(db).assign("c1", c.id, "u1", "u2", utc_now() - timedelta(hours=2), 1)
            return c.id
    cid = asyncio.run(seed())
    assert asyncio.run(deadline_escalation.run_deadline_escalation()) == {"cases": 1, "tasks": 0}
    assert asyncio.run(deadline_escalation.run_deadline_escalation()) == {"cases": 0, "tasks": 0}

    async def events():
        async with sm() as db:
            return [e.event_type for e in (await db.execute(select(m.CaseEvent).where(m.CaseEvent.case_id == cid))).scalars()]
    assert "CASE_ESCALATED" in asyncio.run(events())


def test_outbox_job_sends_pending_rows_written_with_case_changes(sm):
    async def seed():
        async with sm() as db:
            await CasesService(db).create_from_flag("c1", "u1", "f1", "S1")
    asyncio.run(seed())
    assert asyncio.run(outbox_dispatch.run_outbox_dispatch()) == {"sent": 1, "retry": 0, "dead_letter": 0}
    assert asyncio.run(outbox_dispatch.run_outbox_dispatch()) == {"sent": 0, "retry": 0, "dead_letter": 0}


def test_scheduler_registers_all_jobs():
    from scheduler import JOBS, build_scheduler
    sched = build_scheduler()
    assert {j.id for j in sched.get_jobs()} == {name for name, _, _ in JOBS}
    assert {"outbox_dispatch", "deadline_escalation"} <= {j.id for j in sched.get_jobs()}
