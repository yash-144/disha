"""Turn the three-way outcome into a binary training label.

dropout     : 1 if the student dropped out, else 0.
not_on_time : 1 if the student dropped out OR was still enrolled after the
              normal course length (did not graduate on time), else 0.
"""
from __future__ import annotations

import pandas as pd

LABELS = ("dropout", "not_on_time")


def make_label(df: pd.DataFrame, label: str) -> pd.Series:
    if label not in LABELS:
        raise ValueError(f"label must be one of {LABELS}")
    t = df["target"]
    if label == "dropout":
        y = t.eq("Dropout")
    else:
        y = t.isin(["Dropout", "Enrolled"])
    return y.astype(int).rename(label)
