"""Score a snapshot: canonical tables + as-of day -> InsightsPayload (JSON).

    python -m disha_ml.rolling.score --tables <dir> --as-of 120 [--model artifacts_rolling] [--out f.json] [--no-meko]

Library use (what the backend calls):
    payload = score_snapshot(tables, as_of=120)   # tables: dict of DataFrames or a folder path
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional, Union

import joblib
import pandas as pd

from .. import meko_hooks
from . import insights as I
from .evaluate import tiers_per_snapshot
from .features import FEATURES, build_snapshots, split_cohorts
from .schema import load_tables, validate

DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "artifacts_rolling"


def load_bundle(path=None) -> Dict:
    p = Path(path or DEFAULT_MODEL)
    return joblib.load(p / "model.joblib" if p.is_dir() else p)


def score_snapshot(tables: Union[Dict[str, pd.DataFrame], str, Path], as_of: int,
                   bundle: Optional[Dict] = None) -> I.InsightsPayload:
    """Insights for every enrolment still active at day `as_of` (days since term start)."""
    tables = load_tables(tables) if isinstance(tables, (str, Path)) else validate(tables)
    bundle = bundle or load_bundle()
    as_of = int(as_of)
    snaps = build_snapshots(tables, bundle["fixed_fracs"], as_of=as_of)
    model = bundle["model"]
    p = model.predict_proba(snaps[FEATURES])[:, 1]
    scored = tiers_per_snapshot(snaps, p, bundle["cutoffs"], bundle["capacity_share"])
    hist = I.add_previous(scored)
    cur = hist[hist["snapshot_day"] == as_of]
    contrib = I.explain(model, cur[FEATURES], bundle["reference"]) if len(cur) else pd.DataFrame()
    cohorts = split_cohorts(tables)
    students = I.student_insights(hist, contrib, cohorts, as_of) if len(cur) else []
    cohort_out = [I.cohort_insight(c, hist[(hist["course_id"] == k[0]) & (hist["term_id"] == k[1])], as_of)
                  for k, c in cohorts.items()]
    drift = I.drift_report(bundle["psi_reference"], cur[FEATURES])
    model_info = {"bundle_version": bundle["version"], "trained_terms": list(bundle["trained_terms"]),
                  "cutoffs": {k: (v or {}).get("threshold") for k, v in bundle["cutoffs"].items()}}
    payload = I.InsightsPayload(I.SCHEMA_VERSION, as_of, model_info, len(students), students, cohort_out, drift)
    from ..clo.link import add_co_reasons   # optional: only acts when the CO tables are present
    return add_co_reasons(payload, tables)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Score a snapshot and print insights JSON")
    ap.add_argument("--tables", required=True, help="folder with the canonical tables (.csv or .csv.gz)")
    ap.add_argument("--as-of", type=int, required=True, help="day since term start")
    ap.add_argument("--model", default=None, help="artifacts folder (default: ml/artifacts_rolling)")
    ap.add_argument("--out", default=None, help="write JSON here instead of stdout")
    ap.add_argument("--no-meko", action="store_true", help="never talk to Meko")
    a = ap.parse_args(argv)
    if a.no_meko:
        meko_hooks.disable()
    payload = score_snapshot(a.tables, a.as_of, load_bundle(a.model))
    text = payload.to_json(indent=1)
    if a.out:
        Path(a.out).write_text(text)
        print(f"{payload.n_students} students scored -> {a.out}")
    else:
        print(text)
    meko_hooks.record_assessment_updates(payload.to_dict())


if __name__ == "__main__":
    main()
