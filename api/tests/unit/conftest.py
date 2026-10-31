# Lets these tests import `app` when pytest runs from the repo root (make test).
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


# --- shared DB + auth fixtures (SQLite stands in for Postgres) ---
import asyncio
import time
import uuid

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
import app.modules.campus.models  # noqa: F401 - register tables
import app.modules.cases.models  # noqa: F401
from app.modules.campus.models import CampusMembership

CAMPUS, USER = "c1", "u1"


def token(role="mentor", sub=USER):
    return jwt.encode({"roles": [role], "sub": sub, "exp": time.time() + 600}, settings.DISHA_JWT_SECRET,
                      algorithm=settings.DISHA_JWT_ALGORITHM)


def headers(role="mentor", sub=USER, campus=CAMPUS):
    return {"Authorization": f"Bearer {token(role, sub)}", "X-Campus-ID": campus}


@pytest.fixture
def sm(tmp_path):
    """Sessionmaker on a fresh SQLite file with all tables; user u1 is a member of campus c1."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db", poolclass=NullPool)

    async def setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with async_sessionmaker(engine, expire_on_commit=False)() as s:
            s.add(CampusMembership(id=str(uuid.uuid4()), user_id=USER, campus_id=CAMPUS, is_active=True))
            await s.commit()

    asyncio.run(setup())
    yield async_sessionmaker(engine, expire_on_commit=False)
    asyncio.run(engine.dispose())


@pytest.fixture(autouse=True)
def api_db(sm):
    from app.main import app

    async def _get_db():
        async with sm() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)
