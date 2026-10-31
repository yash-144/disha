"""PII guard, catalogue sync, outcome memory, promotion threshold, related/playbook grouping."""
import json
from types import SimpleNamespace as NS

import httpx
import pytest

from disha_meko import catalog, guard, playbook as pb
from test_meko import FakeHttp, FakeSession, make_client


class LoopSession(FakeSession):
    """Keeps added memories so memory_search/promote behave statefully; kb hits are canned."""

    def __init__(self):
        super().__init__()
        self.mem, self.kb = [], []

    async def call_tool(self, name, args):
        if name == "memory_add":
            self.calls.append((name, args))
            m = {"id": f"m{len(self.mem) + 1}", "memory": args["text"]}
            self.mem.append(m)
            return NS(is_error=False, content=[NS(text=json.dumps({"results": [m]}))], structured_content=None)
        if name in ("memory_search", "knowledgebase_search"):
            self.calls.append((name, args))
            rows = self.mem if name == "memory_search" else self.kb
            return NS(is_error=False, content=[NS(text=json.dumps({"results": rows}))], structured_content=None)
        return await super().call_tool(name, args)


async def close(c, n, outcome="improved", iid="mentor_call", codes=("LOW_ATTENDANCE", "FEE_DUES")):
    return await pb.record_outcome(c, case_id=f"case-{n}", outcome=outcome, intervention_id=iid,
                                   reason_codes=list(codes), tier="HIGH", checkpoint="mid_sem", campus_id="c1")


# ---- PII guard ----
def test_guard_finds_and_strips():
    t = "mail a.b@x.edu, call +91 98765 43210, student CS2021-042 and 21CSE042"
    assert set(guard.find_pii(t)) == {"email", "phone", "student_id"}
    assert guard.find_pii(guard.strip_pii(t)) == []
    assert guard.find_pii("Mentor calls within 3 working days. Tier HIGH.") == []
    with pytest.raises(guard.PiiFound):
        guard.check(b"contact asha@x.edu")


# ---- catalogue sync ----
async def test_catalog_sync_one_doc_per_active_intervention(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeHttp)
    FakeHttp.posts = []
    entries = [{"id": "mentor_call", "title": "Call", "reason_codes": ["B", "A"], "description": "Ring CS-042 now"},
               {"id": "old", "active": False}]
    c, s = make_client()
    out = await catalog.sync_catalog(c, entries, "c1")
    assert out == {"uploaded": ["mentor_call"], "failed": [], "skipped_inactive": ["old"]}
    req = s.calls_to("knowledgebase_upload_document")
    assert len(req) == 1 and req[0]["filename"] == "c1__catalogue__mentor_call.md"
    body = FakeHttp.posts[0][2]["file"][1].decode()
    assert body.startswith("doc_type: catalogue | campus_id: c1 | intervention_id: mentor_call | reason_codes: A,B")
    assert "CS-042" not in body


async def test_status_403_is_graceful(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeHttp)

    class NoStatus(FakeSession):
        async def call_tool(self, name, args):
            if name == "knowledgebase_document_status":
                self.calls.append((name, args))
                return NS(is_error=True, content=[NS(text="403 forbidden")], structured_content=None)
            return await super().call_tool(name, args)

    c, _ = make_client(NoStatus())
    res = await c.upload_bytes(b"# hi", "a.md")
    assert res["ok"] is True and res["state"] == "unknown"


# ---- outcome memory + promotion ----
async def test_outcome_memory_is_hashed_and_structured():
    c, s = make_client(LoopSession())
    res = await close(c, 1)
    assert res["memory_saved"] and res["promoted"] == []
    add = s.calls_to("memory_add")[0]
    assert "case-1" not in add["text"] and "case: s_" in add["text"]
    assert "intervention_id: mentor_call | reason_codes: FEE_DUES,LOW_ATTENDANCE" in add["text"]
    meta = json.loads(add["metadata"])
    assert meta["doc_type"] == "outcome" and meta["reason_codes"] == ["FEE_DUES", "LOW_ATTENDANCE"] and meta["tier"] == "HIGH"


async def test_promotion_threshold_and_pattern_match():
    c, s = make_client(LoopSession(), promote_min=3)
    await close(c, 1)
    await close(c, 2, codes=("OTHER",))            # different pattern: not counted
    await close(c, 3, outcome="worse")            # not improved: not counted
    assert (await close(c, 4))["promoted"] == []   # 2 matching improved
    assert s.calls_to("memory_promote") == []
    res = await close(c, 5)                       # 3rd matching improved
    assert res["improved_count"] == 3 and res["promoted"] == ["m1", "m4", "m5"]
    assert s.calls_to("memory_promote")[0]["memory_ids"] == ["m1", "m4", "m5"]


# ---- related + playbook ----
def kb(text, doc="d1", source=None):
    return {"document_id": doc, "chunk_text": text, "metadata_filters": {"source": source} if source else {}}


async def test_related_groups_by_intervention_and_playbook_filters_catalogue():
    c, s = make_client(LoopSession())
    s.kb = [kb("doc_type: catalogue | intervention_id: mentor_call | reason_codes: FEE_DUES,LOW_ATTENDANCE\n\n# Call"),
            kb("doc_type: policy | intervention_id: mentor_call | reason_codes: FEE_DUES\n\nFee relief rule", "d2"),
            kb("doc_type: outcome | intervention_id: mentor_call | reason_codes: FEE_DUES,LOW_ATTENDANCE | tier: HIGH | outcome: improved",
               "d3", source="memory"),
            kb("doc_type: outcome | intervention_id: ghost_scheme | reason_codes: FEE_DUES | tier: HIGH | outcome: improved",
               "d4", source="memory")]
    s.mem = [{"id": "m1", "memory": "doc_type: outcome | intervention_id: mentor_call | reason_codes: FEE_DUES | tier: LOW | outcome: worse"}]
    g = await pb.related(c, reason_codes=["FEE_DUES"])
    assert set(g) == {"mentor_call", "ghost_scheme"}
    assert len(g["mentor_call"]["catalogue"]) == 1 and len(g["mentor_call"]["policy"]) == 1
    assert len(g["mentor_call"]["outcomes"]) == 2
    q = s.calls_to("knowledgebase_search")[0]["query"]
    assert q == "reason_codes: FEE_DUES"

    out = await pb.playbook(c, ["FEE_DUES"], "HIGH", {"mentor_call", "fee_plan"})
    assert [r["intervention_id"] for r in out["suggestions"]] == ["mentor_call"]  # ghost_scheme not in catalogue
    top = out["suggestions"][0]
    assert top["promoted"] and top["improved"] == 1 and top["not_improved"] == 1
    assert top["catalogue_chunks"] and top["policy_chunks"][0]["document_id"] == "d2"
    assert out["dropped_not_in_catalogue"] == 1
