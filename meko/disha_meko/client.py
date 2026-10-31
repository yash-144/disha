"""Fail-safe Meko MCP client.

Every public method returns a harmless value ([] / None / False) when Meko is
disabled, unconfigured, slow or down. Meko must never break training or the API.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
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


def _rows(res: Any) -> list[dict]:
    rows = res.get("results") if isinstance(res, dict) else res
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


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
