"""The Alembic revision creates exactly the tables and columns the models declare."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # make `app` importable from the repo root

pytest.importorskip("alembic")
pytest.importorskip("aiosqlite")
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.database import Base
import app.modules.campus.models  # noqa: F401
import app.modules.cases.models  # noqa: F401


def test_migration_matches_models(tmp_path, monkeypatch):
    api = Path(__file__).resolve().parents[2]
    db = tmp_path / "m.db"
    cfg = Config(str(api / "alembic.ini"))
    cfg.set_main_option("script_location", str(api / "migrations"))
    cfg.attributes["url"] = f"sqlite+aiosqlite:///{db}"
    command.upgrade(cfg, "head")
    insp = inspect(create_engine(f"sqlite:///{db}"))
    for name in ("disha_cases", "disha_case_tasks", "disha_restricted_task_details", "disha_case_events",
                 "disha_case_outcomes", "disha_outbox", "disha_campus_memberships"):
        table = Base.metadata.tables[name]
        assert {c["name"] for c in insp.get_columns(name)} == {c.name for c in table.columns}, name
    command.downgrade(cfg, "base")
    assert "disha_cases" not in inspect(create_engine(f"sqlite:///{db}")).get_table_names()
