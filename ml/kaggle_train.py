"""One-cell Kaggle runner.

In a Kaggle notebook (CPU is enough, no GPU needed; Internet on to clone):
    !git clone https://github.com/yash-144/disha.git
    %cd disha/ml
    !python kaggle_train.py

With no argument it trains on the dataset committed in this repository,
ml/data/processed/data.csv. Other options:
    !python kaggle_train.py /kaggle/input/<folder>/<file>.csv
    !python kaggle_train.py <file>.csv --mapping mapping.json
    !python kaggle_train.py --label not_on_time --model logreg
Outputs go to /kaggle/working/artifacts and /kaggle/working/demo_scored_<cp>.csv
(or ml/artifacts and ml/demo_scored_<cp>.csv when run locally).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import sklearn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from disha_ml.config import CHECKPOINTS, TrainConfig  # noqa: E402
from disha_ml.data import load_dataset, load_mapping  # noqa: E402
from disha_ml.score import load_bundle, score_frame  # noqa: E402
from disha_ml.train import run  # noqa: E402

DEFAULT_DATA = HERE / "data" / "processed" / "data.csv"


def find_csv() -> Path:
    if DEFAULT_DATA.exists():
        return DEFAULT_DATA
    root = Path("/kaggle/input")
    if root.exists():
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
    working = Path("/kaggle/working")
    out = working / "artifacts" if working.exists() else HERE / "artifacts"
    print(f"Data: {data}\nOutput: {out}\nscikit-learn {sklearn.__version__}, pandas {pd.__version__}")
    results = run(str(data), str(out), CHECKPOINTS, TrainConfig(label=a.label, model=a.model), mapping)

    # Demo file: score every student with the semester-1 model; students with no
    # semester-1 record are scored with the admission model (cp0) instead.
    trained = {r["checkpoint"] for r in results}
    demo_cp = "cp1" if "cp1" in trained else results[-1]["checkpoint"]
    raw = load_dataset(data, mapping=mapping)
    scored = score_frame(load_bundle(out / demo_cp), raw)
    gap = scored["tier"] == "NO_DATA"
    if gap.any() and "cp0" in trained:
        scored.loc[gap] = score_frame(load_bundle(out / "cp0"), raw[gap]).values
    scored["actual_outcome"] = raw["target"]
    demo = out.parent / f"demo_scored_{demo_cp}.csv"
    scored.sort_values("risk_probability", ascending=False).to_csv(demo, index=False)
    print(f"Demo scores: {demo}  ({int(gap.sum())} rows scored with cp0; includes training rows, "
          f"for display only — accuracy figures are in each report.md)")


if __name__ == "__main__":
    main()
