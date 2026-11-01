"""Knowledge endpoints (role checks, PII guard), case outcome loop and playbook filtering."""
import json
import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app
from .conftest import headers

import pytest  # noqa: E402
pytestmark = pytest.mark.usefixtures("fake_auth")


class FakeMeko:
    active = True
    last_error = None
    last_memory_id = None

    class cfg:
        datapack = "disha"
        promote_min = 2

    def __init__(self):
        self.uploads, self.deleted, self.promoted, self.mem = [], [], [], []

    def hash_id(self, v):
        return "s_hash"

    async def upload_bytes(self, data, filename, wait=8.0):
        self.uploads.append((filename, data))
        return {"ok": True, "key": "k1", "state": "unknown"}

    async def search_knowledge(self, q, limit=5):
        return [{"document_id": "d1", "chunk_text": "doc_type: policy | intervention_id: mentor_call\n\nrule", "distance": 0.1},
                {"document_id": "d2", "chunk_text": "doc_type: outcome | intervention_id: ghost | reason_codes: FEE_DUES | outcome: improved",
                 "metadata_filters": {"source": "memory"}}]

    async def search_memories(self, q, limit=20):
        return self.mem

    async def delete_document(self, doc_id):
        self.deleted.append(doc_id)
        return True

    async def remember(self, text, tags=None, metadata=None):
        self.mem.append({"id": f"m{len(self.mem) + 1}", "memory": text})
        self.last_memory_id = self.mem[-1]["id"]
        return True

    async def promote(self, ids):
        self.promoted.append(ids)
        return ids


def auth(role):
    return headers(role)  # fake tenancy (see conftest.fake_auth)


CATALOG = {"interventions": [{"id": "mentor_call", "title": "Mentor call"}, {"id": "fee_plan", "active": False}]}


@pytest.fixture
def env(tmp_path, monkeypatch):
    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(CATALOG))
    monkeypatch.setenv("MEKO_CATALOG_PATH", str(p))
    fake = FakeMeko()
    with TestClient(app) as client:
        app.state.meko = fake
        yield client, fake


def upload(client, role, content=b"Scholarship rules apply.", name="rules.md"):
    return client.post("/api/v1/meko/knowledge", headers=auth(role), files={"file": (name, content)},
                       data={"intervention_id": "mentor_call", "reason_codes": "B,A"})


def test_knowledge_role_checks(env):
    client, fake = env
    assert upload(client, "mentor").status_code == 403
    assert client.post("/api/v1/meko/knowledge", files={"file": ("a.md", b"x")}).status_code == 401
    assert client.delete("/api/v1/meko/knowledge/d1", headers=auth("mentor")).status_code == 403
    assert upload(client, "institution_admin").status_code == 200
    name, data = fake.uploads[0]
    assert name == "c1__policy__rules.md"
    assert data.decode().startswith("doc_type: policy | campus_id: c1 | intervention_id: mentor_call | reason_codes: A,B")
    assert client.delete("/api/v1/meko/knowledge/d1", headers=auth("hod")).status_code == 200
    assert fake.deleted == ["d1"]


def test_knowledge_rejects_pii_type_and_size(env, monkeypatch):
    client, fake = env
    assert upload(client, "hod", b"call asha@x.edu").status_code == 422
    assert upload(client, "hod", b"call 98765 43210 now").status_code == 422
    assert upload(client, "hod", b"student CS2021-042").status_code == 422
    assert upload(client, "hod", b"MZ", "x.exe").status_code == 415
    import app.modules.meko.routes as r
    monkeypatch.setattr(r, "KB_MAX_BYTES", 5)
    assert upload(client, "hod", b"too large file").status_code == 413
    assert fake.uploads == []


def test_knowledge_search_returns_document_ids(env):
    client, _ = env
    assert client.get("/api/v1/meko/knowledge/search?q=rules", headers=auth("mentor")).json()["results"][0]["document_id"] == "d1"
    assert client.get("/api/v1/meko/knowledge/search?q=rules").status_code == 401


def test_outcome_loop_promotes_and_playbook_filters_catalogue(env):
    client, fake = env
    body = {"outcome": "improved", "intervention_id": "mentor_call", "reason_codes": ["FEE_DUES"], "tier": "HIGH", "checkpoint": "mid_sem"}
    url = "/api/v1/meko/outcomes"
    assert client.post(url, headers=auth("mentor"), json={**body, "case_id": "case-1", "intervention_id": "fee_plan"}).status_code == 422  # inactive
    assert client.post(url, headers=auth("mentor"), json={**body, "case_id": "case-1"}).json()["recorded"] is True
    assert fake.promoted == []
    client.post(url, headers=auth("mentor"), json={**body, "case_id": "case-2"})
    assert fake.promoted == [["m1", "m2"]]  # MEKO_PROMOTE_MIN=2 on the fake
    assert "case-1" not in fake.mem[0]["memory"]  # only the hashed case id reaches Meko
    assert client.post(url, json={**body, "case_id": "case-3"}).status_code == 401
    r = client.get("/api/v1/meko/playbook?reason_codes=fee_dues&tier=HIGH", headers=auth("mentor")).json()
    assert [s["intervention_id"] for s in r["suggestions"]] == ["mentor_call"]  # 'ghost' not in catalogue
    assert r["suggestions"][0]["title"] == "Mentor call" and r["dropped_not_in_catalogue"] == 1
