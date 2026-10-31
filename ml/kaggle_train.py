"""One-cell Kaggle runner.

In a Kaggle notebook (CPU is enough, no GPU needed):
  1. Add your dataset as input (for example "Predict Students' Dropout and
     Academic Success", or your own CSV).
  2. Upload or clone this `ml/` folder, then run one of:
         !python kaggle_train.py
         !python kaggle_train.py /kaggle/input/<folder>/<file>.csv
         !python kaggle_train.py /kaggle/input/<folder>/<file>.csv --mapping mapping.json
Outputs go to /kaggle/working/artifacts and /kaggle/working/demo_scored_<cp>.csv.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kagaz_ml.config import CHECKPOINTS, TrainConfig  # noqa: E402
from kagaz_ml.data import load_dataset, load_mapping  # noqa: E402
from kagaz_ml.score import load_bundle, score_frame  # noqa: E402
from kagaz_ml.train import run  # noqa: E402


def find_csv() -> Path:
    for root in (Path("/kaggle/input"), HERE / "data"):
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.csv")):
            head = p.open("r", encoding="utf-8-sig").readline().lower()
            if "target" in head and "curricular units" in head:
                return p
    raise SystemExit("Dataset CSV not found. Pass its path as the first argument.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", nargs="?", default=None)
    ap.add_argument("--mapping", default=None)
    ap.add_argument("--label", default="dropout", choices=["dropout", "not_on_time"])
    ap.add_argument("--model", default="hgb", choices=["hgb", "logreg"])
    a = ap.parse_args()
    data = Path(a.data) if a.data else find_csv()
    mapping = load_mapping(a.mapping)
    out = Path("/kaggle/working/artifacts") if Path("/kaggle/working").exists() else HERE / "artifacts"
    print(f"Data: {data}\nOutput: {out}")
    results = run(str(data), str(out), CHECKPOINTS, TrainConfig(label=a.label, model=a.model), mapping)

    # Demo file: score every student with the latest trained early-warning model.
    demo_cp = "cp1" if any(r["checkpoint"] == "cp1" for r in results) else results[-1]["checkpoint"]
    bundle = load_bundle(out / demo_cp)
    raw = load_dataset(data, mapping=mapping)
    scored = score_frame(bundle, raw)
    scored["actual_outcome"] = raw["target"]
    demo = out.parent / f"demo_scored_{demo_cp}.csv"
    scored.sort_values("risk_probability", ascending=False).to_csv(demo, index=False)
    print(f"Demo scores: {demo}  (includes training rows; for display, not for measuring accuracy)")


if __name__ == "__main__":
    main()
