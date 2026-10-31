"""Meko routes and the flag-review trace. Run from api/: pytest tests/unit"""
import time

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app
from .conftest import headers


class FakeMeko:
    active = True
    last_error = None

    class cfg:
        datapack = "disha"

    def __init__(self):
        self.traces = []

    async def list_tools(self):
        return [{"name": "search_memories", "description": "", "params": ["query"]}]

    async def mapping(self):
        return {"recall": "search_memories"}

    async def recall(self, q, k=5):
        return "mentor calls worked"

    async def trace_decision(self, **kw):
        self.traces.append(kw)
        return True


def auth(role="mentor"):
    return headers(role)  # bearer token + X-Campus-ID of a campus u1 belongs to


def test_meko_routes_and_flag_trace():
    fake = FakeMeko()
    with TestClient(app) as client:
        app.state.meko = fake  # replace the lifespan client
        assert client.get("/api/v1/meko/health").json()["reachable"] is True
        assert client.get("/api/v1/meko/tools").status_code == 401
        r = client.post("/api/v1/meko/recall", json={"query": "what worked for similar risk?"}, headers=auth())
        assert r.json()["answer"] == "mentor calls worked"
        r = client.post("/api/v1/cases/flags/review", headers=auth(), json={
            "flag_id": "f1", "student_id": "CS-042", "action": "dismiss", "reason_codes": ["LOW_ATTENDANCE"]})
        assert r.status_code == 200
    assert fake.traces and fake.traces[0]["actor"] == "mentor"
    assert fake.traces[0]["evidence"]["student_id"] == "CS-042"  # hashed later, inside MekoClient
    assert fake.traces[0]["plan"] and "dismiss" in fake.traces[0]["outcome"]


def test_api_starts_without_meko_key(monkeypatch):
    monkeypatch.delenv("MEKO_API_KEY", raising=False)
    with TestClient(app) as client:
        h = client.get("/api/v1/meko/health").json()
        assert h["configured"] is False and h["reachable"] is False
