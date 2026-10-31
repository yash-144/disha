"""Per-student explanation by switching off one feature group at a time.

For each group (for example 'exams taken in semester 1') the group's values are
replaced with those of a typical student (training medians / most common
course) and the student is re-scored. The drop in probability is that group's
contribution. Positive = pushes risk up.

Works for any model and needs no extra library. SHAP is an optional upgrade.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .features import GROUP_TEXT


def reference_values(X_train: pd.DataFrame, categorical: List[str]) -> Dict[str, object]:
    ref: Dict[str, object] = {}
    for c in X_train.columns:
        if c in categorical:
            ref[c] = X_train[c].mode(dropna=True).iloc[0]
        else:
            med = X_train[c].median(skipna=True)
            ref[c] = float(med) if pd.notna(med) else np.nan
    return ref


def group_contributions(model, X: pd.DataFrame, groups: Dict[str, List[str]], ref: Dict[str, object]) -> pd.DataFrame:
    base = model.predict_proba(X)[:, 1]
    out = pd.DataFrame(index=X.index)
    for name, cols in groups.items():
        cols = [c for c in cols if c in X.columns]
        if not cols:
            continue
        Xr = X.copy()
        for c in cols:
            Xr[c] = ref[c]
        out[name] = base - model.predict_proba(Xr)[:, 1]
    return out


def top_factors(contrib_row: pd.Series, k: int = 3, min_effect: float = 0.02) -> List[str]:
    pos = contrib_row[contrib_row >= min_effect].sort_values(ascending=False).head(k)
    return [f"{GROUP_TEXT.get(g, g)} (+{v * 100:.0f} pts)" for g, v in pos.items()]
