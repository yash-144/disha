"""Campus intervention catalogue -> one Meko document per intervention (Meko chunks and indexes it)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .guard import strip_pii

SAFE = re.compile(r"[^A-Za-z0-9_-]+")


def safe(value: str) -> str:
    return SAFE.sub("-", str(value or "")).strip("-") or "default"


def load_catalog(path: str | Path | None) -> list[dict]:
    """JSON list (or {"interventions": [...]}) of {id, title, description, active, ...}. [] if unset/missing."""
    if not path or not Path(path).is_file():
        return []
    data = json.loads(Path(path).read_text("utf-8"))
    rows = data.get("interventions", []) if isinstance(data, dict) else data
    return [r for r in rows if isinstance(r, dict) and r.get("id")]


def active_ids(entries: list[dict]) -> set[str]:
    return {str(e["id"]) for e in entries if e.get("active", True)}


def header(**kv) -> str:
    """The linking line: same keys on every chunk source so keyword/entity search surfaces them together."""
    return " | ".join(f"{k}: {','.join(v) if isinstance(v, (list, tuple)) else v}" for k, v in kv.items() if v)


def entry_markdown(entry: dict, campus_id: str) -> str:
    codes = sorted(entry.get("reason_codes") or [])
    head = header(doc_type="catalogue", campus_id=campus_id, intervention_id=entry["id"], reason_codes=codes)
    body = [f"# {entry.get('title') or entry['id']}", entry.get("description") or ""]
    for k in ("eligibility", "owner_role", "typical_duration", "contraindications"):
        if entry.get(k):
            body.append(f"**{k.replace('_', ' ')}:** {entry[k]}")
    return strip_pii(head + "\n\n" + "\n\n".join(b for b in body if b)) + "\n"


async def sync_catalog(client, entries: list[dict], campus_id: str = "default") -> dict:
    """Upload each active intervention as its own markdown document."""
    campus_id = safe(campus_id)
    out = {"uploaded": [], "failed": [], "skipped_inactive": []}
    for e in entries:
        if not e.get("active", True):
            out["skipped_inactive"].append(str(e["id"]))
            continue
        res = await client.upload_bytes(entry_markdown(e, campus_id).encode(),
                                        f"{campus_id}__catalogue__{safe(e['id'])}.md")
        out["uploaded" if res and res["ok"] else "failed"].append(str(e["id"]))
    return out
