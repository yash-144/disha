"""One-cell Kaggle runner.

In a Kaggle notebook (CPU is enough, no GPU needed; Internet on to clone):
    !git clone https://github.com/yash-144/disha.git
    %cd disha/ml
    !python kaggle_train.py

With no argument it trains on the dataset committed in this repository,
ml/data/processed/data.csv (UCI, Portugal). Other options:
    !python kaggle_train.py --dataset upv          # UPV Spain: train on 2018+2021, test on 2022
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
UPV_DATA = HERE / "data" / "processed" / "upv_first_year.csv"
UPV_RAW = HERE / "data" / "raw" / "upv"


def upv_csv() -> Path:
    """Converted UPV file; built from the Zenodo download if missing (needs Internet)."""
    if not UPV_DATA.exists():
        from disha_ml.converters import upv
        upv.download(UPV_RAW)
        UPV_DATA.parent.mkdir(parents=True, exist_ok=True)
        upv.convert(UPV_RAW).to_csv(UPV_DATA, index=False)
    return UPV_DATA


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
    ap.add_argument("--model", default=None, choices=["hgb", "logreg"])
    ap.add_argument("--dataset", default="uci", choices=["uci", "upv"],
                    help="uci (default) or upv; ignored if a data path is given")
    ap.add_argument("--test-cohort", default=None, help="time-based test cohort (needs cohort_year)")
    a = ap.parse_args()
    if a.data:
        data = Path(a.data)
    elif a.dataset == "upv":
        data = upv_csv()
        # UPV defaults, chosen from the comparison in ml/README.md: logistic regression,
        # trained on earlier intakes and tested on the 2022 intake.
        a.model = a.model or "logreg"
        a.test_cohort = a.test_cohort or "2022"
    else:
        data = find_csv()
    a.model = a.model or "hgb"
    mapping = load_mapping(a.mapping)
    working = Path("/kaggle/working")
    folder = "artifacts_upv" if (a.dataset == "upv" and not a.data) else "artifacts"
    out = (working if working.exists() else HERE) / folder
    print(f"Data: {data}\nOutput: {out}\nscikit-learn {sklearn.__version__}, pandas {pd.__version__}")
    results = run(str(data), str(out), CHECKPOINTS, TrainConfig(label=a.label, model=a.model, test_cohort=a.test_cohort), mapping)

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
    suffix = "_upv" if folder == "artifacts_upv" else ""
    demo = out.parent / f"demo_scored_{demo_cp}{suffix}.csv"
    scored.sort_values("risk_probability", ascending=False).to_csv(demo, index=False)
    print(f"Demo scores: {demo}  ({int(gap.sum())} rows scored with cp0; includes training rows, "
          f"for display only — accuracy figures are in each report.md)")


if __name__ == "__main__":
    main()
