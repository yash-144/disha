import base64
import hashlib
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS

import httpx
import pytest

from disha_meko import MekoClient, MekoConfig, hash_id, scrub
from disha_meko import client as client_mod
from disha_meko import tools as T

STR = {"type": "string"}
OPT = {"anyOf": [{"type": "string"}, {"type": "null"}]}


def tool(tool_name, **props):
    return NS(name=tool_name, description="", inputSchema={"properties": props})


COMMON = dict(conversation_id=STR, agent_id=OPT, datapack_id=OPT)
TOOLS = [
    tool("datapack_list", conversation_id=STR, datapack_id=OPT, query=STR, limit={"type": "integer"}),
    tool("datapack_create", name=STR, conversation_id=STR, datapack_id=OPT),
    tool("conversation_create", agent_id=OPT, title=OPT, metadata=OPT, session_id=STR, datapack_id=OPT, run_id=OPT),
    tool("conversation_add_message", input=STR, output=STR, reasoning=OPT, plan={"type": "array"}, metadata=OPT, seed=OPT, **COMMON),
    tool("conversation_delete", **COMMON),
    tool("memory_add", text=STR, metadata=OPT, messages=OPT, run_id=OPT, **COMMON),
    tool("memory_delete_by_id", memory_id=STR, **COMMON),
    tool("context_search", query=STR, prompt=OPT, limit={"type": "integer"}, force_source=STR, verify={"type": "boolean"}, **COMMON),
    tool("knowledgebase_upload_document", filename=STR, size={"type": "integer"}, content_hash=STR, content_head_base64=STR, **COMMON),
    tool("knowledgebase_document_status", document_key=STR, **COMMON),
    tool("artifact_put", filename=STR, content_base64=STR, content_type=STR, **COMMON),
    tool("track_token_usage", name=STR, input_tokens={"type": "integer"}, output_tokens={"type": "integer"}, model=OPT, conversation_id=STR, datapack_id=OPT),
    tool("knowledgebase_search", query=STR, limit={"type": "integer"}, **COMMON),
    tool("knowledgebase_delete_document", document_id=STR, **COMMON),
    tool("memory_search", query=STR, limit={"type": "integer"}, **COMMON),
    tool("memory_promote", memory_ids={"type": "array"}, **COMMON),
    tool("amp_cluster_create"),
]
DP_ID, CONV_ID = "dp-1", "conv-1"


class FakeSession:
    """Answers the way the real Meko tools do (shapes from the Meko docs)."""

    def __init__(self, datapacks=None):
        self.calls = []
        self.datapacks = [{"datapack_id": DP_ID, "datapack_name": "disha"}] if datapacks is None else datapacks

    async def initialize(self):
        pass

    async def list_tools(self):
        return NS(tools=TOOLS)

    def calls_to(self, name):
        return [a for n, a in self.calls if n == name]

    def names(self):
        return [n for n, _ in self.calls]

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        out = {
            "datapack_list": self.datapacks,
            "datapack_create": {"datapack_id": DP_ID, "datapack_name": args.get("name")},
            "conversation_create": {"id": CONV_ID, "title": args.get("title")},
            "memory_add": {"results": [{"id": "mem-1", "memory": args.get("text")}]},
            "context_search": {"results": {"memory": [{"id": "mem-1", "memory": "mentor calls worked"}],
                                           "knowledge_base": [{"chunk_text": "doc chunk"}],
                                           "conversation": {"hits": [{"output": "past turn"}]}}},
            "knowledgebase_upload_document": {"url": "https://s3.example/bucket", "key": "u/d/h/f.md",
                                              "fields": {"key": "u/d/h/f.md", "policy": "p", "x-amz-security-token": "t"},
                                              "already_uploaded": False},
            "knowledgebase_document_status": {"state": "completed"},
            "memory_promote": {"inserted_ids": list(args.get("memory_ids", [])), "updated_ids": [], "not_found_ids": []},
            "artifact_put": {"artifact_id": "a-1", "content_hash": hashlib.sha256(base64.b64decode(args.get("content_base64", ""))).hexdigest()},
        }.get(name, {"ok": True})
        return NS(is_error=False, content=[NS(text=json.dumps(out))], structured_content=None)


def make_client(session=None, component="disha-ml", **cfg):
    session = session or FakeSession()
    base = dict(api_key="mko_tkn_x", pii_salt="salt")
    base.update(cfg)
    client_mod._DATAPACK_IDS.clear()

    @asynccontextmanager
    async def factory(_cfg):
        yield session

    return MekoClient(MekoConfig(**base), session_factory=factory, component=component), session


# ---- tool mapping ----
def test_default_map_uses_exact_names():
    for op, name in T.DEFAULT_TOOLS.items():
        assert T.resolve(op, TOOLS, {})[0] == name, op
    assert T.DEFAULT_TOOLS["trace_decision"] == "conversation_add_message"
    assert T.DEFAULT_TOOLS["recall"] == "context_search"


def test_keyword_fallback_when_default_missing():
    renamed = [tool("add_memory"), tool("search_memories"), tool("amp_core_budget")]
    assert T.resolve("remember", renamed, {})[0] == "add_memory"
    assert T.resolve("recall", renamed, {})[0] == "search_memories"
    assert T.resolve("save_artifact", renamed, {})[0] is None


def test_override_and_arg_rename():
    name, renames = T.resolve("remember", TOOLS, {"remember": {"tool": "memory_delete_by_id", "args": {"text": "memory_id"}}})
    assert name == "memory_delete_by_id" and renames == {"text": "memory_id"}
    assert T.resolve("remember", TOOLS, {"remember": "nope"})[0] is None


def test_args_fit_schema_and_encode_json_strings():
    t = next(t for t in TOOLS if t.name == "memory_add")
    args = T.build_args(t, {"text": "hi", "datapack_id": DP_ID, "metadata": {"a": 1}, "junk": 1, "limit": None})
    assert args == {"text": "hi", "datapack_id": DP_ID, "metadata": '{"a": 1}'}
    plan_tool = next(t for t in TOOLS if t.name == "conversation_add_message")
    assert T.build_args(plan_tool, {"plan": ["a", "b"]})["plan"] == ["a", "b"]  # arrays stay arrays


# ---- datapack + conversation bootstrap ----
async def test_resolves_datapack_id_and_opens_one_conversation():
    c, s = make_client()
    assert await c.remember("run summary", tags=["ml"]) is True
    assert await c.remember("second") is True
    assert s.names().count("conversation_create") == 1  # once per client/run
    assert s.names()[:2] == ["datapack_list", "conversation_create"]
    assert s.calls_to("conversation_create")[0]["datapack_id"] == DP_ID
    assert s.calls_to("conversation_create")[0]["agent_id"] == "disha-ml"
    add = s.calls_to("memory_add")[0]
    assert add["conversation_id"] == CONV_ID and add["datapack_id"] == DP_ID and add["agent_id"] == "disha-ml"
    assert "[tags: ml]" in add["text"] and json.loads(add["metadata"])["tags"] == ["ml"]
    assert c.last_memory_id == "mem-1" and c.datapack_id == DP_ID


async def test_datapack_created_when_missing_and_id_cached():
    c, s = make_client(FakeSession(datapacks=[]))
    assert await c.ensure_datapack() is True
    assert s.names() == ["datapack_list", "datapack_create"]
    client_mod._DATAPACK_IDS[(c.cfg.url, "disha")] = DP_ID
    c4 = MekoClient(c.cfg, session_factory=c._factory)
    assert c4.datapack_id == DP_ID  # shared id cache skips the lookup


async def test_components_get_distinct_agent_ids():
    for comp in ("disha-api", "disha-worker"):
        c, s = make_client(component=comp)
        await c.remember("x")
        assert s.calls_to("memory_add")[0]["agent_id"] == comp


# ---- operations ----
async def test_recall_uses_context_search_query():
    c, s = make_client()
    out = await c.recall("what worked", k=3)
    call = s.calls_to("context_search")[0]
    assert call["query"] == "what worked" and call["limit"] == 3 and "prompt" not in call
    assert "[memory] mentor calls worked" in out and "[knowledge] doc chunk" in out and "[conversation] past turn" in out


async def test_trace_decision_is_a_conversation_turn():
    c, s = make_client()
    assert await c.trace_decision("pick cutoffs", "because precision", {"k": 1}, actor="ml", outcome="HIGH=0.7",
                                  plan=["step a", "step b"]) is True
    msg = s.calls_to("conversation_add_message")[0]
    assert (msg["input"], msg["output"], msg["reasoning"]) == ("pick cutoffs", "HIGH=0.7", "because precision")
    assert msg["plan"] == ["step a", "step b"] and msg["conversation_id"] == CONV_ID
    meta = json.loads(msg["metadata"])
    assert meta["actor"] == "ml" and meta["evidence"] == {"k": 1} and meta["kind"] == "decision_trace"


async def test_save_artifact_verifies_hash():
    c, s = make_client()
    res = await c.save_artifact("m.json", {"auc": 0.8, "student_id": "42"})
    sent = base64.b64decode(s.calls_to("artifact_put")[0]["content_base64"])
    assert res["verified"] is True and res["content_hash"] == hashlib.sha256(sent).hexdigest()
    assert b'"42"' not in sent and s.calls_to("artifact_put")[0]["content_type"] == "application/json"


async def test_delete_and_token_usage():
    c, s = make_client()
    assert await c.remember("x")
    assert await c.delete_memory("mem-1") and s.calls_to("memory_delete_by_id")[0]["memory_id"] == "mem-1"
    assert await c.token_usage("t", 5, 6, model="m") and s.calls_to("track_token_usage")[0]["input_tokens"] == 5
    assert await c.delete_conversation() and s.calls_to("conversation_delete")[0]["conversation_id"] == CONV_ID


async def test_tool_error_returns_falsy_without_backoff():
    class Err(FakeSession):
        async def call_tool(self, name, args):
            if name == "memory_add":
                self.calls.append((name, args))
                return NS(is_error=False, content=[NS(text='{"error": "read_only_access"}')], structured_content=None)
            return await super().call_tool(name, args)

    c, s = make_client(Err())
    assert await c.remember("x") is False and "read_only_access" in c.last_error
    assert await c.recall("y") != ""  # not backed off


# ---- knowledge upload ----
class FakeHttp:
    posts = []

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    async def post(self, url, data=None, files=None):
        FakeHttp.posts.append((url, data, files))
        return NS(status_code=204, text="")


async def test_upload_knowledge_presigned_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeHttp)
    FakeHttp.posts = []
    f = tmp_path / "note.md"
    f.write_text("# hello " + "x" * 5000)
    c, s = make_client()
    assert await c.upload_knowledge(f) is True
    req = s.calls_to("knowledgebase_upload_document")[0]
    raw = f.read_bytes()
    assert req["size"] == len(raw) and req["content_hash"] == hashlib.sha256(raw).hexdigest()
    assert base64.b64decode(req["content_head_base64"]) == raw[:3072]
    assert "content" not in req
    url, data, files = FakeHttp.posts[0]
    assert url == "https://s3.example/bucket" and list(data) == ["key", "policy", "x-amz-security-token"]
    assert files["file"][1] == raw
    assert s.calls_to("knowledgebase_document_status")[0]["document_key"] == "u/d/h/f.md"
    assert c.last_upload_states["note.md"] == "completed"


async def test_upload_skips_post_when_already_uploaded(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeHttp)
    FakeHttp.posts = []

    class Dup(FakeSession):
        async def call_tool(self, name, args):
            if name == "knowledgebase_upload_document":
                self.calls.append((name, args))
                return NS(is_error=False, content=[NS(text='{"url": "", "key": "k", "already_uploaded": true}')], structured_content=None)
            return await super().call_tool(name, args)

    f = tmp_path / "a.md"
    f.write_text("same")
    c, _ = make_client(Dup())
    assert await c.upload_many([f], root=tmp_path) == {"a.md": True}
    assert FakeHttp.posts == []


async def test_upload_rejects_unsupported_type(tmp_path):
    f = tmp_path / "x.exe"
    f.write_bytes(b"MZ")
    c, s = make_client()
    assert await c.upload_knowledge(f) is False and s.calls == []


# ---- no-op / failure ----
@pytest.mark.parametrize("cfg", [dict(api_key=""), dict(enabled=False)])
async def test_noop_when_inactive(cfg):
    c, s = make_client(**cfg)
    assert await c.remember("x") is False
    assert await c.recall("x") == ""
    assert await c.list_tools() == []
    assert await c.save_artifact("a.json", {}) is None
    assert s.calls == []


async def test_unreachable_does_not_raise_and_backs_off():
    attempts = []

    @asynccontextmanager
    async def boom(_cfg):
        attempts.append(1)
        raise ConnectionError("down")
        yield

    c = MekoClient(MekoConfig(api_key="k"), session_factory=boom)
    assert await c.remember("x") is False
    assert await c.recall("x") == ""  # skipped during backoff
    assert len(attempts) == 1 and "ConnectionError" in c.last_error


async def test_unmapped_tool_is_noop():
    class Bare(FakeSession):
        async def list_tools(self):
            return NS(tools=[tool("ping")])

    c, s = make_client(Bare())
    assert await c.remember("x") is False and s.calls == []


async def test_mapping_reports_every_op():
    c, _ = make_client()
    m = await c.mapping()
    assert set(m) == set(T.DEFAULT_TOOLS) and all(m.values())


# ---- redaction ----
def test_hash_is_salted_and_stable():
    assert hash_id("CS2021-042", "a") == hash_id("CS2021-042", "a")
    assert hash_id("CS2021-042", "a") != hash_id("CS2021-042", "b")
    assert "CS2021" not in hash_id("CS2021-042", "a")
    assert hash_id("CS2021-042", "") == "student-unlinked"


def test_scrub_removes_pii():
    out = scrub({"student_id": "42", "name": "Asha Rao", "note": "mail asha@x.edu or call +91 98765 43210",
                 "nested": [{"roll_no": "R7", "tier": "HIGH"}]}, "salt")
    flat = str(out)
    for leak in ("42'", "Asha", "asha@x.edu", "98765", "R7"):
        assert leak not in flat
    assert out["nested"][0]["tier"] == "HIGH" and out["student_id"].startswith("s_")


async def test_client_scrubs_before_sending():
    c, s = make_client()
    await c.trace_decision("accept flag", "mail a@b.com", {"student_id": "99"}, actor="mentor")
    sent = str(s.calls_to("conversation_add_message")[0])
    assert "a@b.com" not in sent and "'99'" not in sent
