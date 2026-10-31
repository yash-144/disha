"""Fail-safe Meko MCP client.

Every public method returns a harmless value ([] / None / False) when Meko is
disabled, unconfigured, slow or down. Meko must never break training or the API.
"""
from __future__ import annotations

import ast
import asyncio
import base64
import hashlib
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from . import tools as T
from .config import MekoConfig
from .redact import hash_id, scrub

log = logging.getLogger("disha_meko")
USER_AGENT = "meko-mcp-installer/1.0"
BACKOFF_SECONDS = 60  # after a failed connect, skip Meko for a while instead of timing out every call


@asynccontextmanager
async def open_session(cfg: MekoConfig):
    """Connect to the remote MCP server (Streamable HTTP) and yield an initialized session."""
    from mcp import ClientSession

    headers = {"Authorization": f"Bearer {cfg.api_key}", "User-Agent": USER_AGENT}
    try:  # mcp 1.x
        from mcp.client.streamable_http import streamablehttp_client

        transport = streamablehttp_client(cfg.url, headers=headers, timeout=cfg.timeout)
    except ImportError:  # mcp 2.x
        from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

        transport = streamable_http_client(cfg.url, http_client=create_mcp_http_client(headers=headers))
    async with transport as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


_DATAPACK_IDS: dict[tuple[str, str], str] = {}  # (url, datapack name) -> id, shared by every client in the process
TEXT_EXTENSIONS = {".md", ".txt", ".text", ".json", ".csv", ".xml", ".html", ".htm"}
KB_EXTENSIONS = TEXT_EXTENSIONS | {".pdf"}
TERMINAL_STATES = {"completed", "failed", "abandoned", "oversized"}
HEAD_BYTES = 3072  # content_head_base64 sample size required by knowledgebase_upload_document


JOURNEY_AGENT = "disha-journey"  # one agent id for every journey conversation: conversations are agent-owned, so API/ML/worker must share it
HASHED = re.compile(r"^s_[0-9a-f]{12}$")
_JOURNEY_IDS: dict[tuple[str, str, str], str] = {}  # (url, datapack id, student hash) -> conversation id, shared by every client in the process
_WARNED: set[str] = set()


class MekoClient:
    """One client = one component (agent_id) and, lazily, one Meko conversation per run/session.

    Memories go through memory_add; decision traces are turns in the session conversation.
    """

    def __init__(self, cfg: MekoConfig | None = None,
                 session_factory: Callable[[MekoConfig], Any] = open_session,
                 component: str = "disha"):
        self.cfg = cfg or MekoConfig.from_env()
        self.component = component
        self.agent_id = component  # stable per component: disha-api / disha-ml / disha-worker
        self._factory = session_factory  # swapped for a fake in tests
        self._tools: list | None = None
        self._down_until = 0.0
        self._datapack_id = self.cfg.datapack_id or _DATAPACK_IDS.get((self.cfg.url, self.cfg.datapack), "")
        self._conversation_id = ""
        self._journey_listed = False  # conversation_list scanned once per client
        self._journey_touched: set[str] = set()  # students written to by this client (for the volume cap)
        self.last_error: str | None = None
        self.last_memory_id: str | None = None
        self.last_upload_states: dict = {}

    @property
    def active(self) -> bool:
        return self.cfg.active

    @property
    def conversation_id(self) -> str:
        return self._conversation_id

    # ---- plumbing -------------------------------------------------------
    async def _run(self, fn: Callable[[Any], Awaitable[Any]], default: Any = None, timeout: float | None = None) -> Any:
        if not self.active or time.monotonic() < self._down_until:
            return default

        async def go():
            async with self._factory(self.cfg) as session:
                if self._tools is None:
                    self._tools = list((await session.list_tools()).tools)
                return await fn(session)

        try:
            return await asyncio.wait_for(go(), timeout=timeout or self.cfg.timeout * 3)
        except BaseException as exc:  # incl. ExceptionGroup from anyio task groups
            if isinstance(exc, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
                raise
            self.last_error = _describe(exc)
            self._down_until = time.monotonic() + BACKOFF_SECONDS
            log.warning("Meko unavailable, continuing without it (%s)", self.last_error)
            return default

    async def _invoke(self, session: Any, op: str, fields: dict) -> Any:
        """Resolve the op to a tool, fit arguments, call it -> parsed result, or None on any failure."""
        name, renames = T.resolve(op, self._tools or [], self.cfg.tool_map)
        if not name:
            log.warning("Meko: no tool found for '%s'; set MEKO_TOOL_MAP (tools: %s)",
                        op, [t.name for t in self._tools or []])
            return None
        tool = next(t for t in self._tools if t.name == name)
        res = await session.call_tool(name, T.build_args(tool, fields, renames))
        data = _parse(res)
        if _is_error(res) or (isinstance(data, dict) and data.get("error")):
            self.last_error = f"{name}: {_text(res)[:200]}"
            log.warning("Meko tool %s returned an error: %s", name, _text(res)[:200])
            return None
        return data if data is not None else ""

    async def _resolve_datapack(self, session: Any, create: bool = True) -> str:
        """datapack name -> datapack_id (datapack_list, then datapack_create if missing). Cached."""
        if self._datapack_id:
            return self._datapack_id
        boot = str(uuid.uuid4())  # these tools need some conversation_id; a throwaway UUID is accepted
        rows = await self._invoke(session, "list_datapacks", {"conversation_id": boot, "query": self.cfg.datapack})
        found = _find_datapack(rows, self.cfg.datapack)
        if not found and create:
            made = await self._invoke(session, "create_datapack", {"conversation_id": boot, "name": self.cfg.datapack})
            found = _first(made, "datapack_id", "id")
        if found:
            self._datapack_id = found
            _DATAPACK_IDS[(self.cfg.url, self.cfg.datapack)] = found
        return found

    async def _conversation(self, session: Any) -> str:
        """The session conversation for this client, created on first use."""
        if self._conversation_id:
            return self._conversation_id
        if not await self._resolve_datapack(session):
            return ""
        res = await self._invoke(session, "create_conversation", {
            "agent_id": self.agent_id, "datapack_id": self._datapack_id,
            "title": f"{self.component} {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
            "metadata": {"component": self.component, "kind": "session"}})
        self._conversation_id = _first(res, "id", "conversation_id")
        return self._conversation_id

    async def _scoped(self, session: Any, op: str, **fields) -> Any:
        """Call a tool inside the datapack + session conversation, attributed to this component."""
        cid = await self._conversation(session)
        if not cid:
            return None
        return await self._invoke(session, op, {"conversation_id": cid, "datapack_id": self._datapack_id,
                                                "agent_id": self.agent_id, **fields})

    async def _op(self, op: str, **fields) -> Any:
        return await self._run(lambda s: self._scoped(s, op, **fields))

    def _clean(self, obj: Any) -> Any:
        return scrub(obj, self.cfg.pii_salt)

    def hash_id(self, value: Any) -> str:
        return hash_id(value, self.cfg.pii_salt)

    # ---- high-level API -------------------------------------------------
    async def list_tools(self) -> list[dict]:
        async def go(session):
            return [{"name": t.name, "description": (t.description or "").strip()[:120],
                     "params": sorted((T.input_schema(t).get("properties") or {}).keys())}
                    for t in self._tools or []]
        return await self._run(go, default=[])

    async def mapping(self) -> dict:
        """Which tool each logical op resolves to (None = unmapped)."""
        await self.list_tools()
        return {op: T.resolve(op, self._tools or [], self.cfg.tool_map)[0] for op in T.DEFAULT_TOOLS}

    async def ensure_datapack(self) -> bool:
        """Resolve (or create) the datapack and cache its id."""
        return bool(await self._run(self._resolve_datapack, default=""))

    @property
    def datapack_id(self) -> str:
        return self._datapack_id

    async def remember(self, text: str, tags: list[str] | None = None, metadata: dict | None = None) -> bool:
        """Durable fact -> memory_add. Tags go in metadata and are appended to the text so search can find them."""
        text = self._clean(text)
        if tags:
            text = f"{text} [tags: {', '.join(tags)}]"
        meta = {"component": self.component, **(self._clean(metadata) if metadata else {})}
        if tags:
            meta["tags"] = tags
        res = await self._op("remember", text=text, metadata=meta)
        if res is None:
            return False
        self.last_memory_id = _first(res.get("results") if isinstance(res, dict) else res, "id", "memory_id") or None
        return True

    async def recall(self, query: str, k: int = 5) -> str:
        """context_search over memory, knowledge base and past conversation turns -> readable text."""
        res = await self._op("recall", query=self._clean(query), limit=k)
        return _render_context(res) if res is not None else ""

    async def trace_decision(self, decision: str, rationale: str = "", evidence: dict | list | None = None,
                             actor: str = "system", outcome: str = "", plan: list[str] | None = None) -> bool:
        """Record a decision as a turn in the session conversation (conversation_add_message)."""
        meta = {"kind": "decision_trace", "actor": actor, "component": self.component}
        if evidence:
            meta["evidence"] = self._clean(evidence)
        res = await self._op("trace_decision", input=self._clean(decision),
                             output=self._clean(outcome) or f"Decision recorded by {actor}.",
                             reasoning=self._clean(rationale) or None,
                             plan=[self._clean(p) for p in plan] if plan else None, metadata=meta)
        return res is not None

    async def log_conversation(self, messages: list[dict], title: str = "") -> bool:
        """Append user/assistant exchanges ({'role','content'} dicts) to the session conversation."""
        pairs, pending = [], ""
        for m in self._clean(messages):
            if m.get("role") == "assistant" and pending:
                pairs.append((pending, m.get("content", "")))
                pending = ""
            elif m.get("role") != "assistant":
                pending = m.get("content", "")
        ok = bool(pairs)
        for q, a in pairs:
            ok = await self.trace_decision(q, outcome=a, actor=title or "conversation") and ok
        return ok

    async def save_artifact(self, filename: str, data: bytes | str | dict | list,
                            content_type: str = "application/json") -> dict | None:
        """Store a file via artifact_put -> {artifact_id, content_hash, verified}. Dicts/strs are PII-scrubbed first."""
        if isinstance(data, (dict, list)):
            data = json.dumps(self._clean(data), indent=2, default=str)
        if isinstance(data, str):
            data = self._clean(data).encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        res = await self._op("save_artifact", filename=filename, content_type=content_type,
                             content_base64=base64.b64encode(data).decode())
        if not isinstance(res, dict):
            return None
        got = res.get("content_hash")
        return {"artifact_id": res.get("artifact_id"), "content_hash": got, "verified": got == digest}

    async def token_usage(self, name: str, input_tokens: int = 0, output_tokens: int = 0,
                          model: str | None = None) -> bool:
        res = await self._op("token_usage", name=name, input_tokens=input_tokens, output_tokens=output_tokens,
                             model=model)
        return res is not None

    async def delete_memory(self, memory_id: str) -> bool:
        return await self._op("delete_memory", memory_id=memory_id) is not None

    async def delete_conversation(self, conversation_id: str | None = None) -> bool:
        """Delete a conversation (default: this client's session conversation)."""
        cid = conversation_id or self._conversation_id
        if not cid:
            return False
        async def go(session):
            return await self._invoke(session, "delete_conversation", {
                "conversation_id": cid, "agent_id": self.agent_id, "datapack_id": self._datapack_id})
        ok = await self._run(go) is not None
        if ok and cid == self._conversation_id:
            self._conversation_id = ""
        return ok

    # ---- student academic journey: one conversation per student ------------------------
    @property
    def journey_ready(self) -> bool:
        """Journeys are written only when Meko is active AND a salt exists (an unsalted hash of a roll number is guessable)."""
        if not self.active:
            return False
        if not self.cfg.pii_salt:
            if "salt" not in _WARNED:
                _WARNED.add("salt")
                log.warning("Meko journeys are OFF: set MEKO_PII_SALT (a long random secret) so student ids can be hashed")
            return False
        return True

    def journey_hash(self, student: Any) -> str:
        """Raw student id (or an already hashed s_<12 hex>) -> hashed id; '' when there is no salt."""
        if isinstance(student, str) and HASHED.match(student):
            return student
        return self.hash_id(student) if self.cfg.pii_salt else ""

    def journey_clean(self, text: Any, raw_id: Any = None) -> str:
        """Last line of defence for every journey text: the raw id, emails, phone numbers and id-like tokens never leave."""
        t = str(text or "")
        if raw_id is not None and str(raw_id) and not HASHED.match(str(raw_id)):
            t = re.sub(re.escape(str(raw_id)), self.journey_hash(raw_id), t, flags=re.I)
        return " ".join(self._clean(t).split())

    def _journey_key(self, h: str) -> tuple[str, str, str]:
        return (self.cfg.url, self._datapack_id, h)

    async def _journey_scan(self, session: Any) -> None:
        """Fill the cache from conversation_list (titles 'journey:<hash>' / metadata kind=journey), once per client."""
        if self._journey_listed:
            return
        self._journey_listed = True
        for offset in range(0, 2000, 100):
            res = await self._invoke(session, "list_conversations", {
                "agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id, "limit": 100, "offset": offset})
            rows = _conv_rows(res)
            for r in rows:
                h = _journey_student(r)
                cid = str(r.get("id") or r.get("conversation_id") or "")
                if h and cid:
                    _JOURNEY_IDS.setdefault(self._journey_key(h), cid)
            if len(rows) < 100:
                break

    async def _journey_conv(self, session: Any, h: str, create: bool = True) -> str:
        """Conversation id of a student's journey: cache, then conversation_list, then (if create) conversation_create."""
        if not h or not await self._resolve_datapack(session, create=create):
            return ""
        key = self._journey_key(h)
        if key in _JOURNEY_IDS:
            return _JOURNEY_IDS[key]
        await self._journey_scan(session)
        if key in _JOURNEY_IDS or not create:
            return _JOURNEY_IDS.get(key, "")
        if h not in self._journey_touched and len(self._journey_touched) >= self.cfg.journey_max_students:
            log.warning("Meko journey cap reached (MEKO_JOURNEY_MAX_STUDENTS=%d); not opening a journey for %s",
                        self.cfg.journey_max_students, h)
            return ""
        res = await self._invoke(session, "create_conversation", {
            "agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id, "title": f"journey:{h}",
            "session_id": f"journey:{h}",  # deterministic dedup key: a second create reconnects the same conversation
            "metadata": {"kind": "journey", "student": h}})
        cid = _first(res, "id", "conversation_id")
        if cid:
            _JOURNEY_IDS[key] = cid
        return cid

    async def journey_conversation(self, student: Any, create: bool = True) -> str:
        """Get or create the journey conversation 'journey:<hash>' (metadata {kind: journey, student: <hash>}).
        '' when Meko is off, there is no salt, the cap is reached or Meko fails."""
        h = self.journey_hash(student)
        if not h or h == "student-unlinked" or not self.journey_ready:
            return ""
        return await self._run_journey(lambda s: self._journey_conv(s, h, create), default="", timeout=self._journey_timeout()) or ""

    async def _journey_add(self, session: Any, cid: str, turn: dict, h: str, raw: Any) -> bool:
        meta = {"kind": "journey", "student": h, **(turn.get("metadata") or {})}
        fields = {"conversation_id": cid, "agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id,
                  "input": self.journey_clean(turn["input"], raw), "output": self.journey_clean(turn["output"], raw),
                  "reasoning": self.journey_clean(turn.get("reasoning"), raw) or None,
                  "metadata": self._clean(meta), "seed": turn.get("seed")}
        for attempt in (1, 2):  # one retry: a dropped connection must not lose the turn
            try:
                return await self._invoke(session, "trace_decision", fields) is not None
            except Exception as exc:  # noqa: BLE001
                self.last_error = _describe(exc)
                log.warning("Meko journey write failed (attempt %d): %s", attempt, self.last_error)
                await asyncio.sleep(1.5)
        return False

    async def _run_journey(self, fn, default: Any = None, timeout: float | None = None, attempts: int = 3) -> Any:
        """_run with retries for journey calls: a dropped connection (ConnectError/ConnectTimeout) lifts the 60 s
        backoff and is retried after a pause, so a transient network error does not lose a write or empty a read."""
        fail = object()
        for i in range(attempts):
            res = await self._run(fn, default=fail, timeout=timeout)
            if res is not fail:
                return res
            if not self.active or i == attempts - 1:
                break
            self._down_until = 0.0
            await asyncio.sleep(2.0 * (i + 1))
        return default

    def _journey_timeout(self, n_turns: int = 0) -> float:
        """Journey calls are slower than plain ones (~2 s per turn, memory_update/context_search up to ~15 s)."""
        return max(60.0, self.cfg.timeout * 8) + 4 * n_turns

    async def journey_post(self, turns: list[dict], chunk: int = 40) -> int:
        """Post academic-event turns ({student, input, output, reasoning?, metadata?, seed?}) to each student's journey
        conversation, batched over one connection per chunk and rate limited. -> number of turns stored (soft-fails to 0)."""
        if not turns or not self.journey_ready:
            return 0
        done = 0
        for i in range(0, len(turns), chunk):
            part = turns[i:i + chunk]

            async def go(session, part=part):
                n, cids = 0, {}
                for t in part:
                    h = self.journey_hash(t["student"])
                    if not h or h == "student-unlinked":
                        continue
                    if h not in cids:
                        cids[h] = await self._journey_conv(session, h)
                    if not cids[h]:
                        continue
                    self._journey_touched.add(h)
                    n += int(await self._journey_add(session, cids[h], t, h, t["student"]))
                    await asyncio.sleep(self.cfg.journey_delay)
                return n

            # turns carry deterministic seeds, so a replayed chunk after a dropped connection cannot duplicate them
            n = await self._run_journey(go, default=0, timeout=self._journey_timeout(len(part)))
            done += n or 0
        return done

    async def journey_timeline(self, student: Any, limit: int = 100) -> list[dict]:
        """The journey conversation's turns in order, as Meko returned them ([] when off / unknown student)."""
        h = self.journey_hash(student)
        if not h or not self.journey_ready:
            return []

        async def go(session):
            cid = await self._journey_conv(session, h, create=False)
            if not cid:
                return []
            res = await self._invoke(session, "get_conversation", {
                "conversation_id": cid, "agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id,
                "include_messages": True, "limit": limit})
            msgs = (res.get("messages") or res.get("turns") or []) if isinstance(res, dict) else []
            return [{**m, "metadata": _meta_dict(m.get("metadata"))} if "metadata" in m else m for m in msgs if isinstance(m, dict)]
        return await self._run_journey(go, default=[], timeout=self._journey_timeout()) or []

    async def journey_briefing(self, student: Any, question: str | None = None, k: int = 10,
                               meko_enabled: bool = True) -> dict:
        """What Meko recalls about one student, verbatim: {enabled, student, question, items:[{id, source, text}]}.
        Items are exactly what context_search returned (no rewriting), limited to this student. meko_enabled=False
        returns an empty briefing (the Meko on/off comparison)."""
        h = self.journey_hash(student)
        out = {"enabled": bool(meko_enabled), "student": h, "question": question, "items": []}
        if not meko_enabled or not h or not self.journey_ready:
            return out

        async def go(session):
            cid = await self._journey_conv(session, h, create=False)
            fields = {"query": self._clean(question) if question else "academic performance, risk and support history", "limit": k,
                      "agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id,
                      "conversation_id": cid or str(uuid.uuid4())}
            res = await self._invoke(session, "recall", fields)
            mem = []
            if cid:  # memories extracted from this student's own conversation: scoped by run_id, so never another student's
                found = await self._invoke(session, "search_memory", {**fields, "run_id": cid})
                mem = _rows(found)
            return res, cid, mem
        got = await self._run_journey(go, default=None, timeout=self._journey_timeout(5))
        if got:
            out["items"] = _context_items(got[0], h, got[1], got[2])
        return out

    async def correct_memory(self, memory_id: str, text: str) -> bool:
        """Replace a recalled memory's text (memory_update). The new text passes the PII guard first."""
        clean = self.journey_clean(text)
        if not memory_id or not clean:
            return False
        return await self._journey_memory_op("update_memory", memory_id=memory_id, text=clean)

    async def forget_memory(self, memory_id: str) -> bool:
        """Delete a recalled memory for good (memory_delete_by_id)."""
        return bool(memory_id) and await self._journey_memory_op("delete_memory", memory_id=memory_id)

    async def _journey_memory_op(self, op: str, **fields) -> bool:
        async def go(session):
            if not await self._resolve_datapack(session, create=False):
                return None
            return await self._invoke(session, op, {"conversation_id": str(uuid.uuid4()), "agent_id": JOURNEY_AGENT,
                                                    "datapack_id": self._datapack_id, **fields})
        return await self._run_journey(go, timeout=self._journey_timeout()) is not None

    async def erase_student(self, student: Any, max_rounds: int = 5) -> dict:
        """Right to erasure: delete everything Meko holds for one student's journey.

        Extracted memories are linked to the journey only by run_id (= conversation id), are not listed by
        memory_get_all, and survive conversation_delete, so they are found with memory_search and deleted by id
        first. Then the conversation goes. -> {"student", "memories_deleted", "conversation_deleted"}."""
        h = self.journey_hash(student)
        out = {"student": h, "memories_deleted": 0, "conversation_deleted": False}
        if not h or h == "student-unlinked" or not self.journey_ready:
            return out

        async def go(session):
            cid = await self._journey_conv(session, h, create=False)
            if not cid:
                return out
            base = {"agent_id": JOURNEY_AGENT, "datapack_id": self._datapack_id}
            for _ in range(max_rounds):  # search returns top hits only, so repeat until nothing is left
                ids = set()
                for q in _ERASE_QUERIES:
                    rows = _rows(await self._invoke(session, "search_memory", {
                        **base, "conversation_id": cid, "run_id": cid, "query": q, "limit": 100}))
                    ids |= {m["id"] for m in rows if m.get("id") and _same_id(m.get("run_id"), cid)}
                if not ids:
                    break
                for mid in ids:
                    if await self._invoke(session, "delete_memory", {**base, "conversation_id": cid, "memory_id": mid}) is not None:
                        out["memories_deleted"] += 1
            r = await self._invoke(session, "delete_conversation", {**base, "conversation_id": cid})
            out["conversation_deleted"] = r is not None
            _JOURNEY_IDS.pop(self._journey_key(h), None)
            return out
        return await self._run_journey(go, default=out, timeout=self._journey_timeout(40)) or out

    async def delete_journey(self, student: Any) -> bool:
        """Delete a student's journey and its extracted memories (see erase_student)."""
        return (await self.erase_student(student))["conversation_deleted"]

    # ---- knowledge upload (presigned S3 POST) ----------------------------
    def _prepare_upload(self, path: Path) -> tuple[bytes, str] | None:
        return self._prepare_bytes(path.read_bytes(), path.name) if path.suffix.lower() in KB_EXTENSIONS else \
            log.warning("Meko: %s is not an accepted knowledge file type", path.name)

    def _prepare_bytes(self, data: bytes, filename: str) -> tuple[bytes, str] | None:
        if Path(filename).suffix.lower() not in KB_EXTENSIONS:
            return None
        if Path(filename).suffix.lower() in TEXT_EXTENSIONS:  # redact before it leaves DISHA; Meko needs UTF-8
            data = self._clean(data.decode("utf-8", errors="replace")).encode("utf-8")
        return data, filename

    async def _upload_one(self, session: Any, data: bytes, filename: str) -> str | None:
        """Request the presigned POST, send the bytes. -> document key (None = failed)."""
        res = await self._scoped(
            session, "upload_knowledge", filename=filename, size=len(data),
            content_hash=hashlib.sha256(data).hexdigest(),
            content_head_base64=base64.b64encode(data[:HEAD_BYTES]).decode())
        if not isinstance(res, dict):
            return None
        if res.get("already_uploaded"):
            return res.get("key") or ""
        fields = res.get("fields") or {}
        if not res.get("url") or not fields:
            self.last_error = "upload_knowledge: response had no url/fields"
            return None
        import httpx

        async with httpx.AsyncClient(timeout=60) as http:  # every signed field, in order, file last
            r = await http.post(res["url"], data=fields, files={"file": (filename, data)})
        if r.status_code not in (200, 201, 204):
            self.last_error = f"S3 POST {r.status_code}: {r.text[:200]}"
            log.warning("Meko knowledge upload of %s failed: %s", filename, self.last_error)
            return None
        return res.get("key") or ""

    async def _status(self, session: Any, key: str) -> str:
        res = await self._scoped(session, "upload_status", document_key=key)
        return str(res.get("state", "")) if isinstance(res, dict) else ""

    async def upload_knowledge(self, path: str | Path, wait: float = 8.0) -> bool:
        """Upload one file to the datapack knowledge base and poll indexing briefly. Team-visible: callers must opt in."""
        p = Path(path)
        if p.suffix.lower() not in KB_EXTENSIONS:
            log.warning("Meko: %s is not an accepted knowledge file type", p.name)
            return False
        return bool((await self.upload_bytes(p.read_bytes(), p.name, wait) or {}).get("ok"))

    async def upload_bytes(self, data: bytes, filename: str, wait: float = 8.0) -> dict | None:
        """Upload in-memory content (Meko chunks and indexes it). -> {ok, key, state}; state may be 'unknown'
        when knowledgebase_document_status is not permitted (403 on some accounts), which counts as ok."""
        prepared = self._prepare_bytes(data, filename)
        if not prepared:
            return None
        data, filename = prepared

        async def go(session):
            key = await self._upload_one(session, data, filename)
            if key is None:
                return {"ok": False, "key": "", "state": "failed"}
            deadline = time.monotonic() + wait
            state = await self._status(session, key) if key else "completed"
            while state and state not in TERMINAL_STATES and time.monotonic() < deadline:
                await asyncio.sleep(1.5)
                state = await self._status(session, key)
            self.last_upload_states[filename] = state or "unknown"
            return {"ok": state not in ("failed", "abandoned", "oversized"), "key": key, "state": state or "unknown"}
        return await self._run(go, default=None, timeout=self.cfg.timeout * 3 + wait + 60)

    # ---- knowledge base + memory search/promote ----------------------------
    async def search_knowledge(self, query: str, limit: int = 5) -> list[dict]:
        """knowledgebase_search -> hits ({document_id, chunk_text, ...}); promoted memories show up here too."""
        return _rows(await self._op("kb_search", query=self._clean(query), limit=limit))

    async def delete_document(self, document_id: str) -> bool:
        return await self._op("delete_document", document_id=document_id) is not None

    async def search_memories(self, query: str, limit: int = 20) -> list[dict]:
        return _rows(await self._op("search_memory", query=self._clean(query), limit=limit))

    async def promote(self, memory_ids: list[str]) -> list[str]:
        """memory_promote (one-way, owner/maintainer only) -> ids moved to shared knowledge ([] on failure/403)."""
        res = await self._op("promote", memory_ids=list(memory_ids))
        return [str(i) for k in ("inserted_ids", "updated_ids") for i in (res.get(k) or [])] if isinstance(res, dict) else []

    async def upload_many(self, paths: list[Path], root: Path | None = None) -> dict:
        """Upload several files over one connection, then check each status once. -> {path: ok}"""
        async def go(session):
            out, keys = {}, {}
            for p in paths:
                name = str(p.relative_to(root)) if root else p.name
                prepared = self._prepare_upload(p)
                try:
                    key = await self._upload_one(session, prepared[0], name.replace("/", "__")) if prepared else None
                except Exception as exc:  # noqa: BLE001 - one bad file must not stop the rest
                    self.last_error = _describe(exc)
                    key = None
                out[name] = key is not None
                if key:
                    keys[name] = key
            for name, key in keys.items():
                state = await self._status(session, key) if key else "completed"
                self.last_upload_states[name] = state or "unknown"
                if state in ("failed", "abandoned", "oversized"):
                    out[name] = False
            return out
        return await self._run(go, default={}, timeout=self.cfg.timeout * 3 + 45 * max(1, len(paths)))


_ERASE_QUERIES = ("student", "assessment score class median", "risk tier", "admission entry baseline",
                  "term summary course", "mentor note", "intervention case outcome")


def _same_id(a: Any, b: Any) -> bool:
    """Meko ids may come back with or without dashes."""
    return bool(a) and str(a).replace("-", "") == str(b).replace("-", "")


def _rows(res: Any) -> list[dict]:
    rows = res.get("results") if isinstance(res, dict) else res
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _conv_rows(res: Any) -> list[dict]:
    if isinstance(res, dict):
        res = res.get("conversations") or res.get("results") or res.get("items") or []
    return [r for r in res if isinstance(r, dict)] if isinstance(res, list) else []


def _meta_dict(meta: Any) -> Any:
    """Meko returns metadata as a JSON or Python-repr string; give back a dict when it parses, else the value as is."""
    if isinstance(meta, str):
        for parse in (json.loads, ast.literal_eval):
            try:
                out = parse(meta)
            except (ValueError, SyntaxError):
                continue
            if isinstance(out, dict):
                return out
    return meta


def _journey_student(row: dict) -> str:
    """Hashed student of a listed conversation, from metadata.student or a 'journey:<hash>' title."""
    meta = _meta_dict(row.get("metadata"))
    if isinstance(meta, dict) and meta.get("kind") == "journey" and HASHED.match(str(meta.get("student", ""))):
        return str(meta["student"])
    title = str(row.get("title") or "")
    return title[len("journey:"):] if title.startswith("journey:") and HASHED.match(title[8:]) else ""


def _context_items(res: Any, h: str, cid: str, mem_rows: list[dict]) -> list[dict]:
    """context_search + run-scoped memory rows -> [{id, source, text}], text untouched. Only items from this student's
    journey conversation: memories carry run_id = the conversation id, so another student's memories are dropped."""
    norm = cid.replace("-", "")
    items, seen = [], set()

    def add(id_, source, text):
        if text and (id_ or text) not in seen:
            seen.add(id_ or text)
            items.append({"id": str(id_ or ""), "source": source, "text": str(text)})
    r = (res.get("results") if isinstance(res.get("results"), dict) else res) if isinstance(res, dict) else {}
    own = lambda row: isinstance(row, dict) and norm and str(row.get("run_id") or row.get("meko_conversation_id") or "").replace("-", "") == norm
    for m in mem_rows + [m for m in r.get("memory") or [] if own(m)]:
        add(m.get("id"), "memory", m.get("memory") or m.get("text"))
    conv = r.get("conversation") or {}
    for hit in (conv.get("hits") if isinstance(conv, dict) else conv) or []:
        if isinstance(hit, dict) and (own({"run_id": hit.get("conversation_id") or hit.get("session_id")}) or h in json.dumps(hit, default=str)):
            add(hit.get("id") or hit.get("message_id"), "conversation", hit.get("output") or hit.get("text") or json.dumps(hit, default=str))
    return items


def _is_error(res: Any) -> bool:
    return bool(getattr(res, "is_error", False) or getattr(res, "isError", False))


def _parse(res: Any) -> Any:
    """CallToolResult -> JSON value (dict/list), or the plain text if it is not JSON."""
    text = _text(res)
    try:
        data = json.loads(text)
    except ValueError:
        data = getattr(res, "structured_content", None) or getattr(res, "structuredContent", None) or text
    if isinstance(data, dict) and list(data) == ["result"]:
        data = data["result"]
    return data


def _first(obj: Any, *keys: str) -> str:
    """First non-empty value for any of keys, looking into a list's first row."""
    if isinstance(obj, list):
        obj = obj[0] if obj else {}
    if isinstance(obj, dict):
        for k in keys:
            if obj.get(k):
                return str(obj[k])
    return ""


def _find_datapack(rows: Any, name: str) -> str:
    if isinstance(rows, dict):
        rows = rows.get("datapacks") or []
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict) and name in (row.get("datapack_name"), row.get("name")):
            return str(row.get("datapack_id") or row.get("id") or "")
    return ""


def _render_context(res: Any) -> str:
    """context_search response -> '[memory] ...' / '[knowledge] ...' / '[conversation] ...' lines."""
    if not isinstance(res, dict):
        return str(res)
    r = res.get("results") if isinstance(res.get("results"), dict) else res
    lines = [f"[memory] {m.get('memory') or m.get('text') or m}" for m in r.get("memory") or []]
    lines += [f"[knowledge] {k.get('chunk_text') or k}" for k in r.get("knowledge_base") or []]
    conv = r.get("conversation") or {}
    for h in (conv.get("hits") if isinstance(conv, dict) else conv) or []:
        body = h if isinstance(h, str) else (h.get("text") or h.get("output") or json.dumps(h, default=str))
        lines.append(f"[conversation] {str(body)[:400]}")
    return "\n".join(lines)


def _describe(exc: BaseException) -> str:
    """Unwrap anyio ExceptionGroups to the underlying error (e.g. HTTP 401)."""
    while getattr(exc, "exceptions", None):
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"


def _text(res: Any) -> str:
    """Flatten an MCP CallToolResult into plain text."""
    parts = [getattr(c, "text", "") for c in getattr(res, "content", None) or []]
    return "\n".join(p for p in parts if p) or json.dumps(
        getattr(res, "structured_content", None) or getattr(res, "structuredContent", None) or "")


class MekoSync:
    """Blocking wrapper for sync callers (ML CLIs, worker threads)."""

    def __init__(self, client: MekoClient | None = None, component: str = "disha"):
        self.client = client or MekoClient(component=component)

    @property
    def active(self) -> bool:
        return self.client.active

    def __getattr__(self, name):
        attr = getattr(self.client, name)
        if not asyncio.iscoroutinefunction(attr):
            return attr
        return lambda *a, **kw: run_sync(attr(*a, **kw))


def run_sync(coro):
    """asyncio.run, but safe when a loop is already running (uses a helper thread)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coro).result()
