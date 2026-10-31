"""Metrics reported for every trained checkpoint."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from .signal import assign_tiers


def score_metrics(y, p) -> Dict[str, float]:
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    return {
        "n": int(len(y)),
        "base_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, np.clip(p, 0, 1))) if p.max() <= 1 else float("nan"),
    }


def calibration_table(y, p, bins: int = 10) -> list:
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p, dtype=float)})
    df["bin"] = pd.cut(df["p"], np.linspace(0, 1, bins + 1), include_lowest=True)
    g = df.groupby("bin", observed=True).agg(n=("y", "size"), predicted=("p", "mean"), observed=("y", "mean"))
    return [
        {"bin": str(i), "n": int(r.n), "predicted": round(float(r.predicted), 3), "observed": round(float(r.observed), 3)}
        for i, r in g.iterrows()
    ]


def signal_metrics(y, p, rule_counts, cutoffs, capacity_share) -> Dict:
    y = np.asarray(y)
    tier, signal, capped = assign_tiers(p, rule_counts, cutoffs, capacity_share)
    positives = max(int(y.sum()), 1)
    out = {
        "signals": int(signal.sum()),
        "signal_rate": float(signal.mean()),
        "signal_precision": float(y[signal].mean()) if signal.any() else None,
        "signal_recall": float(y[signal].sum() / positives),
        "capped": int(capped.sum()),
        "tiers": {},
    }
    for t in ("HIGH", "MEDIUM", "WATCH", "ON_TRACK"):
        m = tier == t
        out["tiers"][t] = {
            "n": int(m.sum()),
            "share": float(m.mean()),
            "observed_rate": float(y[m].mean()) if m.any() else None,
        }
    return out


def _age_band(age: pd.Series) -> pd.Series:
    return pd.cut(pd.to_numeric(age, errors="coerce"), [0, 20, 25, 200], labels=["<=20", "21-25", ">25"]).astype(str)


def fairness_report(y, signal, audit: pd.DataFrame, min_group: int = 30) -> Dict:
    """Signal rate, false-positive rate and miss rate per group of each audit column."""
    y = np.asarray(y)
    signal = np.asarray(signal, dtype=bool)
    cols = {}
    for c in audit.columns:
        cols[c] = _age_band(audit[c]) if c == "age_at_enrollment" else audit[c].astype(str)
    report = {}
    for c, groups in cols.items():
        rows = []
        for g in sorted(groups.unique()):
            m = (groups == g).to_numpy()
            if m.sum() < min_group:
                continue
            neg, pos = m & (y == 0), m & (y == 1)
            rows.append({
                "group": g,
                "n": int(m.sum()),
                "signal_rate": float(signal[m].mean()),
                "false_positive_rate": float(signal[neg].mean()) if neg.any() else None,
                "miss_rate": float((~signal[pos]).mean()) if pos.any() else None,
            })
        fprs = [r["false_positive_rate"] for r in rows if r["false_positive_rate"] is not None]
        ratio = None
        if len(fprs) >= 2 and min(fprs) > 0:
            ratio = float(max(fprs) / min(fprs))
        report[c] = {"groups": rows, "fpr_ratio_max_min": ratio}
    return report
