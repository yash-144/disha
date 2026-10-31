"""Score a cohort with a trained checkpoint and write one row per student.

Usage:
    python -m kagaz_ml.score --model artifacts/cp1 --input students.csv --output scored.csv

The input uses the same column headers as the training CSV; a 'Target'
column is not needed. Columns named student_id, roll_no or name are passed
through to the output for display only; they are never model inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd

from .data import clean, load_mapping, map_columns, read_csv
from .explain import group_contributions, top_factors
from .features import build_features
from .rules import evaluate_rules
from .signal import assign_tiers

PASSTHROUGH = ("student_id", "roll_no", "name")


def load_bundle(model_dir: str | Path) -> dict:
    model_dir = Path(model_dir)
    path = model_dir / "model.joblib"
    manifest_path = model_dir / "manifest.json"
    if manifest_path.exists():
        expected = json.loads(manifest_path.read_text())["model_sha256"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Model file hash {actual} does not match manifest {expected}; refusing to load.")
    return joblib.load(path)


def score_frame(bundle: dict, raw: pd.DataFrame) -> pd.DataFrame:
    """raw: cleaned dataframe with canonical column names."""
    cp = bundle["checkpoint"]
    feats = bundle["features"]
    X = build_features(raw, cp)[feats["numeric"] + feats["categorical"]]
    model = bundle["model"]
    p = model.predict_proba(X)[:, 1]
    fired = [evaluate_rules(raw.loc[i], cp, bundle["rules"]) for i in raw.index]
    tier, signal, capped = assign_tiers(p, [len(f) for f in fired], bundle["cutoffs"], bundle["capacity_share"])
    contrib = group_contributions(model, X, bundle["groups"], bundle["reference"])
    out = pd.DataFrame(index=raw.index)
    out["checkpoint"] = cp
    out["risk_probability"] = p.round(3)
    out["tier"] = tier
    out["signal"] = signal
    out["capacity_capped"] = capped
    out["rule_reasons"] = ["; ".join(r["text"] for r in f) for f in fired]
    out["rule_codes"] = [",".join(r["code"] for r in f) for f in fired]
    out["model_factors"] = ["; ".join(top_factors(contrib.loc[i])) for i in raw.index]
    if not bundle.get("approved", False):
        out["note"] = "model not approved by release check; show for review only"
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Score students with a trained checkpoint.")
    ap.add_argument("--model", required=True, help="checkpoint folder, e.g. artifacts/cp1")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="scored.csv")
    ap.add_argument("--mapping", default=None,
                    help="mapping JSON; defaults to the mapping saved with the model at training time")
    a = ap.parse_args(argv)
    bundle = load_bundle(a.model)
    mapping = load_mapping(a.mapping) if a.mapping else bundle.get("mapping")
    raw_in = read_csv(a.input)
    ids = raw_in[[c for c in raw_in.columns if str(c).strip().lower() in PASSTHROUGH]]
    raw = clean(map_columns(raw_in, require_target=False, mapping=mapping), mapping)
    scored = pd.concat([ids, score_frame(bundle, raw)], axis=1)
    scored.sort_values("risk_probability", ascending=False).to_csv(a.output, index=False)
    counts = scored["tier"].value_counts().to_dict()
    print(f"Scored {len(scored)} students with {bundle['checkpoint']}: {counts}; signals={int(scored['signal'].sum())} -> {a.output}")


if __name__ == "__main__":
    main()
