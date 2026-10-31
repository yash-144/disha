"""Optional Meko hooks: recall prior experiments, store run summaries and decision traces.

Does nothing unless the `disha_meko` package is installed and MEKO_API_KEY is
set. Never raises: Meko must not be able to break training or scoring.
Run summaries are aggregate-only; per-student academic-journey turns use hashed ids (see record_assessment_updates).
"""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List

try:
    from disha_meko import MekoSync
    from disha_meko import journey as J
    from disha_meko.client import run_sync
except ImportError:  # Meko is optional
    MekoSync = J = run_sync = None

_client = None
_disabled = False


def disable() -> None:
    """Called by the --no-meko flag."""
    global _disabled
    _disabled = True


def _meko():
    global _client
    if _disabled or MekoSync is None:
        return None
    if _client is None:
        _client = MekoSync(component="disha-ml")  # one client = one Meko conversation per train/score run
    return _client if _client.active else None


def is_active() -> bool:
    return _meko() is not None


def _guard(fn):
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as exc:  # noqa: BLE001
            print(f"[meko] skipped: {exc}")
    return wrapper


@_guard
def recall_prior_runs(label: str, model: str, data_name: str, k: int = 5) -> None:
    """Print similar past experiments before training starts."""
    m = _meko()
    if not m:
        return
    text = m.recall(f"DISHA ML training run label={label} model={model} dataset={data_name}", k)
    if text:
        print("Prior experiments from Meko:\n" + "\n".join("  " + ln for ln in text.splitlines()[:25]))


def _fairness_summary(fairness: Dict) -> Dict:
    return {col: rep.get("fpr_ratio_max_min") for col, rep in (fairness or {}).items()}


@_guard
def record_training(results: List[Dict], cfg, data_path: str, out_dir: str) -> None:
    """One memory with the run summary plus one decision trace for the chosen cutoffs."""
    m = _meko()
    if not m or not results:
        return
    data_name = os.path.basename(str(data_path))
    cps = []
    for r in results:
        t, s = r["test_metrics"], r["test_signal"]
        cps.append({
            "checkpoint": r["checkpoint"], "roc_auc": round(t["roc_auc"], 3), "pr_auc": round(t["pr_auc"], 3),
            "signal_precision": s.get("signal_precision"), "signal_recall": s.get("signal_recall"),
            "signal_rate": s.get("signal_rate"), "approved": r["release"]["approved"],
            "cutoffs": r["cutoffs"], "fairness_fpr_ratio": _fairness_summary(r["fairness_test"]),
        })
    summary = (f"DISHA ML run: dataset={data_name}, label={cfg.label}, model={cfg.model}, "
               f"calibration={cfg.calibration}, test_cohort={cfg.test_cohort}, checkpoints saved under {out_dir}. "
               + "; ".join(f"{c['checkpoint']}: ROC AUC {c['roc_auc']}, PR AUC {c['pr_auc']}, "
                           f"approved={c['approved']}, cutoffs={c['cutoffs']}" for c in cps))
    m.remember(summary, tags=["ml", "training-run", cfg.label, cfg.model], metadata={"dataset": data_name, "checkpoints": cps})
    m.trace_decision(
        decision=f"Tier cutoffs chosen for {cfg.label} / {cfg.model}",
        rationale=f"Cutoffs picked from out-of-fold calibrated probabilities at HIGH precision target "
                  f"{cfg.tiers.high_precision} with capacity share {cfg.tiers.capacity_share}.",
        outcome="; ".join(f"{c['checkpoint']}: {c['cutoffs']} (approved={c['approved']})" for c in cps),
        plan=["Calibrate out-of-fold probabilities.",
              "Pick the HIGH cutoff at the precision target.",
              "Cap flagged students at the capacity share.",
              "Run the release check on the held-out test cohort."],
        evidence={"dataset": data_name, "checkpoints": cps}, actor="disha_ml.train")
    for r in results:  # aggregate manifest + metrics JSON, kept exactly as written
        manifest = Path(out_dir) / r["checkpoint"] / "manifest.json"
        if manifest.exists():
            m.save_artifact(f"disha-{r['checkpoint']}-manifest.json", json.loads(manifest.read_text()))
    print("[meko] run summary, threshold decision and manifests recorded")


@_guard
def record_scoring(bundle: Dict, scored) -> None:
    """Aggregate-only trace of a scoring run: counts per tier, capacity cap. No student rows."""
    m = _meko()
    if not m:
        return
    counts = {str(k): int(v) for k, v in scored["tier"].value_counts().items()}
    evidence = {"checkpoint": bundle["checkpoint"], "students_scored": int(len(scored)),
                "tier_counts": counts, "signals": int(scored["signal"].sum()),
                "capacity_capped": int(scored["capacity_capped"].sum()),
                "capacity_share": bundle.get("capacity_share"), "model_approved": bool(bundle.get("approved"))}
    m.trace_decision(decision=f"Scoring run at {bundle['checkpoint']}: {evidence['signals']} students flagged for review",
                     rationale="Tiers from calibrated risk and rule hits, limited by the capacity cap. "
                               "Flags are evidence for humans; no case is opened automatically.",
                     outcome=f"Tier counts: {counts}",
                     plan=["Score every student with the checkpoint.", "Assign tiers from risk and rule hits.",
                           "Apply the capacity cap."],
                     evidence=evidence, actor="disha_ml.score")


_threads: List[threading.Thread] = []


def flush(timeout: float = 600.0) -> None:
    """Wait for background journey writes (the CLI calls this implicitly: the writer threads are not daemons)."""
    for t in list(_threads):
        t.join(timeout)
    _threads[:] = [t for t in _threads if t.is_alive()]


def _write_journey(client, turns: List[Dict]) -> None:
    try:
        n = run_sync(client.journey_post(turns))
        print(f"[meko] {n}/{len(turns)} journey turns recorded")
    except Exception as exc:  # noqa: BLE001 - Meko must never break scoring
        print(f"[meko] journey write skipped: {exc}")


@_guard
def record_assessment_updates(payload: Dict) -> int:
    """Academic-journey turns after a rolling scoring run.

    Every scored student-assessment becomes an `assessment_update` turn in that student's own Meko conversation
    (`journey:<hashed id>`), plus a `tier_change` turn when the tier moved and a `drift_event` turn per drift event.
    Written in a background thread, batched and rate limited, capped at MEKO_JOURNEY_MAX_STUDENTS students.
    Needs MEKO_PII_SALT (without it nothing is written, with a warning). Returns the number of turns queued.
    """
    m = _meko()
    if not m or J is None:
        return 0
    client = getattr(m, "client", m)
    if not client.journey_ready:
        print("[meko] journeys skipped: set MEKO_PII_SALT to hash student ids")
        return 0
    cap = client.cfg.journey_max_students
    turns = J.turns_from_insights(payload, cap)
    total = len({s["student_id"] for s in payload.get("students", [])})
    if total > cap:
        print(f"[meko] {total} students scored; journeys limited to {cap} (MEKO_JOURNEY_MAX_STUDENTS)")
    if not turns:
        return 0
    t = threading.Thread(target=_write_journey, args=(client, turns), name="meko-journey")  # non-daemon: finishes before exit
    _threads.append(t)
    t.start()
    print(f"[meko] {len(turns)} journey turns queued in the background")
    return len(turns)


# ---- course (CO) memories -------------------------------------------------------------
# Aggregate-only: no student ids or marks, just course, term, section, CO levels and gaps.
LEARNING_PROMOTE_MIN = 2     # promote a teaching learning once it improved a CO in this many terms/sections
PREFIX = re.compile(r"^(?P<course>\S+) (?P<term>\S+)(?: sec (?P<section>\S+))?: ")


def _tags_in(text: str) -> List[str]:
    m = re.search(r"\[tags: ([^\]]*)\]", text)
    return [t.strip() for t in m.group(1).split(",")] if m else []


def parse_course_summary(text: str):
    """Read back a course-summary memory -> {course, term, section, levels{co: level}}, or None."""
    m = PREFIX.match(text or "")
    if not m or "course-summary" not in _tags_in(text):
        return None
    levels = {}
    body = re.sub(r"\s*\[tags:.*$", "", text[m.end():]).rstrip(".")
    for seg in body.split("; "):
        g = re.match(r"^(\S+) .*?attainment level (\d)", seg)
        if g:
            levels[g.group(1)] = int(g.group(2))
    return {"course": m["course"], "term": m["term"], "section": m["section"], "levels": levels}


def _clean_desc(d) -> str:
    return (d or "").replace(";", ",").replace("[", "(").replace("]", ")")


def _co_seg(co: str, desc: str, level: int) -> str:
    return f"{co} {_clean_desc(desc)} attainment level {level}".replace("  ", " ")


def course_memories(payload: Dict) -> List[Dict]:
    """Pure: payload -> memories to write ({text, tags, metadata}). Reads only aggregate sections."""
    if not payload.get("co_attainment"):
        return []
    course, term = payload["course_id"], payload["term_id"]
    cos = {c["co_id"]: c for c in payload["co_attainment"]}
    base = ["ml", f"course:{course}", f"term:{term}"]

    def prefix(sec=None):
        return f"{course} {term}" + (f" sec {sec}" if sec else "")

    def mem(sec, segs, kind):
        text = f"{prefix(sec)}: " + ("; ".join(segs) if segs else "no CO below level 2") + "."
        return {"text": text, "tags": ["course-summary"] + base + ([f"sec:{sec}"] if sec else []),
                "metadata": {"kind": kind, "course_id": course, "term_id": term, "section": sec}}

    out, segs = [], []                                  # class level
    for co, c in cos.items():
        if c["level"] is not None and (c["level"] <= 1 or c["gap_type"] in ("teaching_gap", "student_gap")):
            segs.append(_co_seg(co, c["description"], c["level"]))
            gaps = [i["question_id"] for i in payload["items"] if i["question_id"] in c["weak_questions"]
                    and i["gap_type"] == "teaching_gap"]
            segs += [f"teaching gap on {q}" for q in gaps[:2]]      # keep the memory short
            if c["gap_type"] == "student_gap":
                segs.append(f"student gap on {co}")
    segs += [f"misconception {m['question_id']} option {m['option']} {m['share_pct']:.0f}%"
             for m in payload["misconceptions"] if m["flagged"]]
    out.append(mem(None, segs, "course_summary"))
    by_sec: Dict[str, List[str]] = {}                   # one memory per section
    for comp in payload["section_comparison"]:
        for r in comp["sections"]:
            segs = by_sec.setdefault(r["section"], [])
            if r["level"] <= 1:
                segs.append(_co_seg(comp["co_id"], cos[comp["co_id"]]["description"], r["level"]))
            if r["trend"] in ("improving", "declining"):
                segs.append(f"{comp['co_id']} {r['trend']} ({r['delta_pts']:+.0f} pts)")
    out += [mem(sec, sg, "course_summary") for sec, sg in sorted(by_sec.items())]
    for l in payload["learnings"]:                      # teaching actions that raised a CO level
        if not l["improved"]:
            continue
        act = l["action"] or "a recorded teaching action"
        slug = re.sub(r"[^a-z0-9]+", "-", act.lower()).strip("-") or "action"
        out.append({"text": f"{prefix(l['section'])}: {l['co_id']} {_clean_desc(cos[l['co_id']]['description'])} improved from "
                            f"level {l['before_level']} to {l['after_level']} after {act} ({l['before_pct']:.0f}% to {l['after_pct']:.0f}%).",
                    "tags": ["course-learning"] + base + [f"co:{l['co_id']}", f"action:{slug}", "outcome:improved"],
                    "metadata": {"kind": "course_learning", "course_id": course, "term_id": term, "section": l["section"],
                                 "co_id": l["co_id"], "action": slug}})
    return out


def _row_text(r: Dict) -> str:
    return str(r.get("memory") or r.get("text") or r.get("chunk_text") or "")


def _promote_if_recurring(m, mem: Dict) -> List[str]:
    """Promote a learning's memories once the same CO + action improved in >= LEARNING_PROMOTE_MIN terms/sections."""
    tags = [t for t in mem["tags"] if t.startswith(("course:", "co:", "action:", "outcome:"))]
    seen = {(mem["metadata"]["term_id"], mem["metadata"]["section"])}
    ids = {str(m.last_memory_id)} if getattr(m, "last_memory_id", None) else set()
    for r in m.search_memories("course-learning " + " ".join(tags), 50):
        txt, p = _row_text(r), PREFIX.match(_row_text(r))
        if p and r.get("id") and "course-learning" in _tags_in(txt) and all(t in _tags_in(txt) for t in tags):
            seen.add((p["term"], p["section"]))
            ids.add(str(r["id"]))
    return m.promote(sorted(ids)) if len(seen) >= LEARNING_PROMOTE_MIN and ids else []


@_guard
def recall_course_history(course_id: str, k: int = 8) -> List[Dict]:
    """Past-term memories for a course, exactly as Meko returned them: [{id, source, text}].

    Shown as `context.recalled` in the CLO payload so the UI can display what Meko recalled.
    Memory hits have source "memory"; promoted learnings come back from the knowledge base ("knowledge").
    """
    m = _meko()
    if not m:
        return []
    q = f"course-summary course-learning course:{course_id}"
    out = [{"id": str(r.get("id") or ""), "source": "memory", "text": _row_text(r)} for r in m.search_memories(q, k)]
    out += [{"id": str(r.get("document_id") or r.get("id") or ""), "source": "knowledge", "text": _row_text(r)}
            for r in m.search_knowledge(q, k)]
    return [h for h in out if h["text"] and course_id in h["text"]]


@_guard
def record_course_learnings(payload: Dict) -> int:
    """Aggregate memories per course, term and section, plus teaching-action learnings (promoted when recurring).

    Never reads or sends student ids. Returns the number of memories written (0 when Meko is off).
    """
    m = _meko()
    if not m:
        return 0
    n = 0
    for mem in course_memories(payload):
        if not m.remember(mem["text"], tags=mem["tags"], metadata=mem["metadata"]):
            continue
        n += 1
        if mem["metadata"]["kind"] == "course_learning":
            promoted = _promote_if_recurring(m, mem)
            if promoted:
                print(f"[meko] learning for {mem['metadata']['co_id']} recurred; promoted {len(promoted)} memories")
    print(f"[meko] {n} course memories recorded")
    return n
