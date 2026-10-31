"""Optional Meko hooks: recall prior experiments, store run summaries and decision traces.

Does nothing unless the `disha_meko` package is installed and MEKO_API_KEY is
set. Never raises: Meko must not be able to break training or scoring.
Only aggregate numbers are sent, never per-student data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List

try:
    from disha_meko import MekoSync
except ImportError:  # Meko is optional
    MekoSync = None

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


def _update_text(s: Dict) -> str:
    """One short narrative line: no raw tables, no student id, marks only as the headline mean/median."""
    snap, risk = s["snapshot"], s["risk"]
    mean, med = snap.get("mean_score"), snap.get("class_median_score")
    marks = f"mean {mean:.0f}% (class median {med:.0f}%)" if mean is not None and med is not None else "no marks yet"
    tier = f"{risk['previous_tier']}→{risk['tier']}" if risk.get("previous_tier") and risk["previous_tier"] != risk["tier"] \
        else f"{risk['tier']} (unchanged)"
    why = [r["text"] for r in s["reasons"][:2]] + [e["text"] for e in s["drift_events"]][:1]
    return (f"Assessment update (day {s['as_of_day']}, {s.get('last_assessment') or 'no assessment yet'}): {marks}; "
            f"risk {tier}" + (f"; {'; '.join(why)}." if why else "."))


@_guard
def record_assessment_updates(payload: Dict) -> int:
    """Academic-story memories after a rolling scoring run.

    One short memory per student whose tier changed or who had a drift event; nothing otherwise.
    Students are keyed by hashed id so their updates can be searched as a journey.
    Returns the number of memories written (0 when Meko is off).
    """
    m = _meko()
    if not m:
        return 0
    n = 0
    for s in payload.get("students", []):
        risk = s["risk"]
        changed = risk.get("previous_tier") is not None and risk["previous_tier"] != risk["tier"]
        if not (changed or s["drift_events"]):
            continue
        sid = m.hash_id(s["student_id"])
        journey = [] if sid == "student-unlinked" else [f"journey:{sid}"]
        m.remember(_update_text(s), tags=["ml", "assessment-update", risk["tier"].lower()] + journey,
                   metadata={"kind": "assessment_update", "student": sid, "course_id": s["course_id"],
                             "term_id": s["term_id"], "day": s["as_of_day"], "tier": risk["tier"],
                             "previous_tier": risk.get("previous_tier"),
                             "drift_events": [e["code"] for e in s["drift_events"]]})
        n += 1
    print(f"[meko] {n} assessment-update memories recorded")
    return n
