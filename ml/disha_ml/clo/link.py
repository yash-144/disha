"""Link to the rolling risk model: per-student CO features become a reason in the insights payload.

The OULAD model is NOT retrained on these: OULAD has no question-level data. The two features
(`weakest_co_pct`, `n_cos_below_target`) only join the model once a college supplies CO data and a
model is trained on it. Until then they are shown as a plain reason (effect_pts = 0: not a model effect).
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from ..rolling.insights import InsightsPayload, Reason
from .analyze import student_co_features


def has_co_data(tables: Dict[str, pd.DataFrame]) -> bool:
    q, r = tables.get("questions"), tables.get("question_results")
    return q is not None and r is not None and len(q) > 0 and len(r) > 0


def add_co_reasons(payload: InsightsPayload, tables: Dict[str, pd.DataFrame]) -> InsightsPayload:
    """Append 'Weak on CO3 (Recursion): 35%' to students who are below target on a CO. Safe when CO data is absent."""
    if not has_co_data(tables):
        return payload
    try:
        feats = {}
        for key in {(s.course_id, s.term_id) for s in payload.students}:
            f = student_co_features(tables, key[0], key[1], as_of=payload.as_of_day)
            feats[key] = f.set_index("student_id") if len(f) else None
        for s in payload.students:
            f = feats.get((s.course_id, s.term_id))
            if f is None or s.student_id not in f.index or f.loc[s.student_id, "n_cos_below_target"] < 1:
                continue
            row = f.loc[s.student_id]
            weak = row["weak_cos"][0]
            d = f" ({weak['description']})" if weak["description"] else ""
            s.reasons.append(Reason("co_attainment", f"Weak on {weak['co_id']}{d}: {weak['pct']:.0f}%", 0.0,
                                    {"weakest_co_pct": float(row["weakest_co_pct"]),
                                     "n_cos_below_target": float(row["n_cos_below_target"])}))
    except Exception as exc:  # noqa: BLE001 - CO data must never break risk scoring
        print(f"[clo] CO reasons skipped: {exc}")
    return payload
