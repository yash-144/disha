"""Map logical operations to real Meko MCP tools, and fit arguments to their schemas.

Resolution order for each op: MEKO_TOOL_MAP override, then DEFAULT_TOOLS (the
exact names Meko ships), then keyword discovery over the live tool list as a
fallback for renamed tools. Arguments use the real Meko names; build_args only
drops what a tool's schema does not accept and JSON-encodes where it wants a string.
"""
from __future__ import annotations

import json
import re
from typing import Any

# logical op -> exact Meko tool name (see docs/architecture/MEKO_INTEGRATION.md)
DEFAULT_TOOLS = {
    "list_datapacks": "datapack_list",
    "create_datapack": "datapack_create",
    "create_conversation": "conversation_create",
    "delete_conversation": "conversation_delete",
    "remember": "memory_add",
    "delete_memory": "memory_delete_by_id",
    "recall": "context_search",
    "trace_decision": "conversation_add_message",
    "log_conversation": "conversation_add_message",
    "upload_knowledge": "knowledgebase_upload_document",
    "upload_status": "knowledgebase_document_status",
    "kb_search": "knowledgebase_search",
    "delete_document": "knowledgebase_delete_document",
    "search_memory": "memory_search",
    "promote": "memory_promote",
    "save_artifact": "artifact_put",
    "token_usage": "track_token_usage",
}

# Fallback keyword rules: a tool needs one "subject" token and one "verb" token, and no "avoid" token.
RULES = {
    "list_datapacks": {"subject": {"datapack", "datapacks"}, "verb": {"list", "get", "all"}, "avoid": {"create", "delete"}},
    "create_datapack": {"subject": {"datapack"}, "verb": {"create", "new", "add"}, "avoid": set()},
    "create_conversation": {"subject": {"conversation", "session"}, "verb": {"create", "start", "new"}, "avoid": {"delete", "list", "get"}},
    "delete_conversation": {"subject": {"conversation"}, "verb": {"delete", "remove"}, "avoid": {"message"}},
    "remember": {"subject": {"memory", "memories", "remember"}, "verb": {"add", "create", "store", "save", "write", "remember", "put"}, "avoid": {"search", "retrieve", "recall", "list", "delete", "get", "query", "find", "update", "promote"}},
    "delete_memory": {"subject": {"memory", "memories"}, "verb": {"delete", "remove"}, "avoid": {"all"}},
    "recall": {"subject": {"context", "memory", "memories", "recall"}, "verb": {"search", "retrieve", "recall", "query", "find"}, "avoid": {"add", "create", "store", "delete", "upload"}},
    "trace_decision": {"subject": {"message", "decision", "trace"}, "verb": {"add", "record", "log", "create"}, "avoid": {"search", "list", "get", "delete"}},
    "log_conversation": {"subject": {"message", "messages", "conversation"}, "verb": {"add", "log", "record", "append"}, "avoid": {"search", "list", "get", "delete", "create"}},
    "upload_knowledge": {"subject": {"knowledgebase", "knowledge", "document"}, "verb": {"upload"}, "avoid": {"search", "status", "delete"}},
    "upload_status": {"subject": {"knowledgebase", "document", "knowledge"}, "verb": {"status"}, "avoid": {"upload", "delete"}},
    "save_artifact": {"subject": {"artifact", "file"}, "verb": {"put", "upload", "save", "store"}, "avoid": {"get"}},
    "token_usage": {"subject": {"token", "tokens"}, "verb": {"usage", "track"}, "avoid": set()},
}

# a logical argument name -> alternative property names, tried only if the real name is absent
ARG_ALIASES = {
    "text": ["text", "content", "memory", "message", "body"],
    "query": ["query", "q", "search", "question", "prompt"],
    "limit": ["limit", "k", "top_k", "max_results"],
    "datapack_id": ["datapack_id", "datapack", "pack_id", "project_id"],
}


def _tokens(name: str) -> set[str]:
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    return {t for t in re.split(r"[^a-zA-Z0-9]+", name.lower()) if t}


def pick_tool(op: str, tool_names: list[str]) -> str | None:
    """Best keyword match for a logical op, or None."""
    rule = RULES.get(op)
    if not rule:
        return None
    best, best_score = None, 0
    for name in tool_names:
        tk = _tokens(name)
        if name.startswith("amp_") or tk & rule["avoid"] or not tk & rule["subject"]:
            continue
        verbs = tk & rule["verb"]
        if not verbs:
            continue
        score = 2 * len(tk & rule["subject"]) + len(verbs) - 0.01 * len(tk)  # prefer short names
        if score > best_score:
            best, best_score = name, score
    return best


def resolve(op: str, tools: list[Any], tool_map: dict) -> tuple[str | None, dict]:
    """-> (tool name, explicit arg renames). Override, then exact default, then keyword discovery."""
    names = [t.name for t in tools]
    ov = tool_map.get(op)
    if isinstance(ov, str):
        return (ov if ov in names else None), {}
    if isinstance(ov, dict) and ov.get("tool") in names:
        return ov["tool"], ov.get("args", {})
    default = DEFAULT_TOOLS.get(op)
    if default in names:
        return default, {}
    return pick_tool(op, names), {}


def _types(prop: dict) -> set[str]:
    out = {prop["type"]} if isinstance(prop.get("type"), str) else set()
    for sub in prop.get("anyOf") or []:
        out |= _types(sub)
    return out


def _coerce(prop: dict, value: Any) -> Any:
    """Meko takes metadata/messages as JSON strings; encode structured values when the schema wants a string."""
    types = _types(prop)
    if isinstance(value, (dict, list, tuple)) and "string" in types and not types & {"object", "array"}:
        return json.dumps(value, default=str)
    return value


def build_args(tool: Any, fields: dict, renames: dict | None = None) -> dict:
    """Fit logical fields (real Meko argument names) to the tool's input schema."""
    renames = renames or {}
    props = input_schema(tool).get("properties") or {}
    if not props:  # no schema: send as given, rename where overridden
        return {renames.get(k, k): v for k, v in fields.items() if v is not None}
    args: dict = {}
    for logical, value in fields.items():
        if value is None:
            continue
        target = renames.get(logical)
        if target is None:
            candidates = [logical] + ARG_ALIASES.get(logical, [])
            target = next((a for a in candidates if a in props and a not in args), None)
        if target:
            args[target] = _coerce(props.get(target) or {}, value)
    return args


def input_schema(tool) -> dict:
    """Tool input schema; mcp 1.x calls it inputSchema, 2.x input_schema."""
    return getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None) or {}
