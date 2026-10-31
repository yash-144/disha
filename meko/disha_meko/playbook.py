"""Outcome loop: closed case -> memory -> recurring good outcomes promoted -> playbook filtered to the catalogue.

Exact relations (intervention <-> reason code <-> outcome counts) belong in Postgres; Meko only
holds the text memory/chunks, linked by shared keys (see catalog.header).
"""
from __future__ import annotations

import re
from collections import defaultdict

from .catalog import header

OUTCOMES = ("improved", "no_change", "worse")
KV = re.compile(r"(\w+): ([^|\n]*)")


def parse(text: str) -> dict:
    """'intervention_id: X | reason_codes: A,B | ...' -> {'intervention_id': 'X', 'reason_codes': ['A','B'], ...}"""
    d = {k: v.strip() for k, v in KV.findall(text or "")}
    d["reason_codes"] = sorted(c for c in d.get("reason_codes", "").split(",") if c)
    return d


def _text(row: dict) -> str:
    return str(row.get("memory") or row.get("text") or row.get("chunk_text") or "")


def outcome_text(outcome, intervention_id, reason_codes, tier, checkpoint, campus_id, case_hash) -> str:
    return header(doc_type="outcome", campus_id=campus_id, intervention_id=intervention_id,
                  reason_codes=sorted(set(reason_codes)), tier=tier, checkpoint=checkpoint,
                  outcome=outcome, case=case_hash)


async def record_outcome(client, *, case_id, outcome, intervention_id, reason_codes, tier=None,
                         checkpoint=None, campus_id="default", min_count: int | None = None) -> dict:
    """Save the outcome as a memory (hashed case id only); promote if the pattern keeps improving."""
    codes = sorted(set(reason_codes))
    meta = {"doc_type": "outcome", "campus_id": campus_id, "intervention_id": intervention_id,
            "reason_codes": codes, "tier": tier, "checkpoint": checkpoint, "outcome": outcome}
    text = outcome_text(outcome, intervention_id, codes, tier, checkpoint, campus_id, client.hash_id(case_id))
    saved = await client.remember(text, tags=["outcome", outcome], metadata={k: v for k, v in meta.items() if v})
    res = {"memory_saved": saved, "improved_count": 0, "promoted": []}
    if saved and outcome == "improved":
        res.update(await maybe_promote(client, intervention_id, codes, min_count))
    return res


async def maybe_promote(client, intervention_id, reason_codes, min_count: int | None = None) -> dict:
    """If the same intervention + reason-code pattern improved >= N times, memory_promote those memories."""
    n = min_count or client.cfg.promote_min
    codes = sorted(set(reason_codes))
    rows = await client.search_memories(
        header(doc_type="outcome", intervention_id=intervention_id, reason_codes=codes, outcome="improved"), 50)
    ids = {str(r["id"]) for r in rows if r.get("id") and (p := parse(_text(r))).get("outcome") == "improved"
           and p.get("intervention_id") == intervention_id and p["reason_codes"] == codes}
    if client.last_memory_id:  # the one just written may not be indexed yet
        ids.add(client.last_memory_id)
    promoted = await client.promote(sorted(ids)) if len(ids) >= n else []
    return {"improved_count": len(ids), "promoted": promoted}


async def related(client, intervention_id=None, reason_codes=None, limit: int = 10) -> dict:
    """knowledgebase_search + memory_search on the shared keys, grouped by intervention_id."""
    q = header(intervention_id=intervention_id, reason_codes=sorted(set(reason_codes or [])))
    kb = await client.search_knowledge(q, limit)
    mem = await client.search_memories(q, limit)
    groups: dict = defaultdict(lambda: {"catalogue": [], "policy": [], "outcomes": []})
    for row, promoted in [(r, bool((r.get("metadata_filters") or {}).get("source") == "memory")) for r in kb] + \
                         [(r, False) for r in mem]:
        p = parse(_text(row))
        g = groups[p.get("intervention_id") or intervention_id or "unlinked"]
        kind = p.get("doc_type")
        if kind == "outcome":
            g["outcomes"].append({"outcome": p.get("outcome"), "reason_codes": p["reason_codes"],
                                  "tier": p.get("tier"), "promoted": promoted})
        elif kind == "catalogue":
            g["catalogue"].append(row.get("chunk_text"))
        else:
            g["policy"].append({"document_id": row.get("document_id"), "chunk_text": _text(row)[:500]})
    return dict(groups)


async def playbook(client, reason_codes, tier, catalog_ids: set[str]) -> dict:
    """Suggested interventions for a risk profile, ranked by improved outcomes, limited to the active catalogue (AI-07)."""
    codes = set(reason_codes)
    groups = await related(client, None, sorted(codes), 20)
    ranked, dropped = [], 0
    for iid, g in groups.items():
        outs = [o for o in g["outcomes"] if codes & set(o["reason_codes"])]
        if not outs:
            continue
        if iid not in catalog_ids:
            dropped += 1
            continue
        ranked.append({"intervention_id": iid, "improved": sum(o["outcome"] == "improved" for o in outs),
                       "not_improved": sum(o["outcome"] != "improved" for o in outs),
                       "same_tier": sum(o["tier"] == tier for o in outs if tier),
                       "promoted": any(o["promoted"] for o in outs),
                       "catalogue_chunks": g["catalogue"][:1], "policy_chunks": g["policy"][:3]})
    ranked.sort(key=lambda r: (r["improved"] - r["not_improved"], r["promoted"], r["same_tier"]), reverse=True)
    return {"suggestions": ranked, "dropped_not_in_catalogue": dropped, "catalogue_size": len(catalog_ids)}
