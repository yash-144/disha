"""Evaluation helpers for the rolling model: metrics, tiers per snapshot, lead time, size."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from ..evaluate import fairness_report, score_metrics
from ..signal import assign_tiers
from .features import rule_flags
from .schema import AUDIT_COLUMNS

SNAP = ["course_id", "term_id", "snapshot_day"]


def ece(y, p, bins: int = 10) -> float:
    """Expected calibration error: weighted gap between predicted and observed rate per bin."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    b = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum((b == i).mean() * abs(p[b == i].mean() - y[b == i].mean()) for i in range(bins) if (b == i).any()))


def tiers_per_snapshot(df: pd.DataFrame, p, cutoffs: Dict, capacity_share: float) -> pd.DataFrame:
    """Tier + signal for each row; the capacity cap is applied inside each (course, term, day) batch."""
    out = df.copy()
    out["p"] = np.asarray(p, float)
    out["rule_n"] = rule_flags(out).sum(axis=1).to_numpy()
    out["tier"], out["signal"] = "ON_TRACK", False
    out["capped"] = False
    for _, idx in out.groupby(SNAP, sort=False).indices.items():
        sub = out.iloc[idx]
        tier, sig, capped = assign_tiers(sub["p"].to_numpy(), sub["rule_n"].to_numpy(), cutoffs, capacity_share)
        out.iloc[idx, out.columns.get_loc("tier")] = tier
        out.iloc[idx, out.columns.get_loc("signal")] = sig
        out.iloc[idx, out.columns.get_loc("capped")] = capped
    return out


def headline(y, p) -> Dict:
    m = score_metrics(y, p)
    y, p = np.asarray(y), np.asarray(p)
    base = max(y.mean(), 1 - y.mean())
    m.update(ece=ece(y, p), accuracy=float(((p >= 0.5) == y).mean()), majority_accuracy=float(base))
    return m


def auc_by_term_fraction(df: pd.DataFrame, p, fracs) -> list:
    """The 'how early can we catch them' curve: AUC on the fixed-day snapshot at each term fraction."""
    out = []
    for f in fracs:
        m = (df["frac_tag"] == f).to_numpy()
        y = df.loc[m, "at_risk"].to_numpy()
        ok = m.sum() > 0 and 0 < y.sum() < len(y)
        out.append({"term_fraction": f, "n": int(m.sum()), "base_rate": float(y.mean()) if m.any() else None,
                    "roc_auc": float(roc_auc_score(y, np.asarray(p)[m])) if ok else None})
    return out


def tier_table(sc: pd.DataFrame) -> Dict:
    """Row-level and student-level precision/recall per tier (sc = output of tiers_per_snapshot)."""
    pos = max(int(sc["at_risk"].sum()), 1)
    rows = {}
    for t in ("HIGH", "MEDIUM", "WATCH", "ON_TRACK"):
        m = sc["tier"] == t
        rows[t] = {"n": int(m.sum()), "share": float(m.mean()), "precision": float(sc.loc[m, "at_risk"].mean()) if m.any() else None,
                   "recall": float(sc.loc[m, "at_risk"].sum() / pos)}
    s = sc["signal"]
    rows["SIGNAL (HIGH+MEDIUM)"] = {"n": int(s.sum()), "share": float(s.mean()),
                                    "precision": float(sc.loc[s, "at_risk"].mean()) if s.any() else None,
                                    "recall": float(sc.loc[s, "at_risk"].sum() / pos)}
    ev = sc.groupby(["student_id", "course_id", "term_id"]).agg(ever=("signal", "max"), y=("at_risk", "max"))
    rows["EVER SIGNALLED (per student)"] = {
        "n": int(ev["ever"].sum()), "share": float(ev["ever"].mean()),
        "precision": float(ev.loc[ev["ever"], "y"].mean()) if ev["ever"].any() else None,
        "recall": float(ev.loc[ev["ever"], "y"].sum() / max(ev["y"].sum(), 1))}
    return rows


def lead_time(sc: pd.DataFrame, withdrawals: pd.DataFrame) -> Dict:
    """Days between a student's first HIGH/MEDIUM signal and their withdrawal."""
    w = withdrawals.groupby(["student_id", "course_id", "term_id"])["day"].min().rename("w_day")
    wd = sc[sc["outcome"].astype(str).str.lower() == "withdrawn"].groupby(["student_id", "course_id", "term_id"]).size().index
    w = w.reindex(wd).dropna()
    first = sc[sc["signal"]].groupby(["student_id", "course_id", "term_id"])["snapshot_day"].min()
    seen = sc.groupby(["student_id", "course_id", "term_id"]).size().index
    w = w[w.index.isin(seen)]  # withdrawn before the first snapshot: never scorable
    lead = (w - first.reindex(w.index)).dropna()
    return {"withdrawn_scorable": int(len(w)), "withdrawn_signalled": int(len(lead)),
            "detection_rate": float(len(lead) / max(len(w), 1)),
            "median_days": float(lead.median()) if len(lead) else None,
            "p25_days": float(lead.quantile(0.25)) if len(lead) else None,
            "p75_days": float(lead.quantile(0.75)) if len(lead) else None}


def fairness(sc: pd.DataFrame, students: pd.DataFrame) -> Dict:
    aud = sc[["student_id"]].merge(students[["student_id"] + [c for c in AUDIT_COLUMNS if c in students]], on="student_id", how="left")
    aud = aud.drop(columns="student_id").fillna("unknown")
    return fairness_report(sc["at_risk"].to_numpy(), sc["signal"].to_numpy(), aud)


def parameter_count(model) -> Dict:
    """Exact size: tree split nodes + leaves of every boosted tree, plus isotonic calibration points."""
    splits = leaves = cal = trees = 0
    for cc in model.calibrated_classifiers_:
        for stage in cc.estimator.named_steps["clf"]._predictors:
            for tree in stage:
                nodes = tree.nodes
                leaves += int(nodes["is_leaf"].sum())
                splits += int((~nodes["is_leaf"].astype(bool)).sum())
                trees += 1
        cal += sum(len(c.X_thresholds_) for c in cc.calibrators)
    return {"folds": len(model.calibrated_classifiers_), "trees": trees, "split_nodes": splits, "leaves": leaves,
            "calibration_points": cal, "total": splits + leaves + cal}
