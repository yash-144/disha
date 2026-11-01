"""Build model features for each checkpoint.

A checkpoint only sees data that exists at that point in time:
  cp0  admission data only
  cp1  + semester 1 results
  cp2  + semester 2 results and semester-to-semester change

Protected / audit columns (gender, age, displaced, special needs) are never
included. test_features.py enforces both rules.
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from .config import CHECKPOINTS

CATEGORICAL = ["course"]


def _ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    out = num / den.where(den > 0)
    return out.astype(float)


def _semester(df: pd.DataFrame, s: str) -> pd.DataFrame:
    enrolled = df[f"{s}_enrolled"]
    out = pd.DataFrame(index=df.index)
    out[f"{s}_enrolled"] = enrolled
    out[f"{s}_approved"] = df[f"{s}_approved"]
    out[f"{s}_credited"] = df[f"{s}_credited"]
    out[f"{s}_grade"] = df[f"{s}_grade"]                      # NaN when nothing passed
    out[f"{s}_no_grade"] = df[f"{s}_grade"].isna().astype(int)
    out[f"{s}_no_units"] = (enrolled <= 0).astype(int)
    out[f"{s}_pass_rate"] = _ratio(df[f"{s}_approved"], enrolled)
    out[f"{s}_attempt_rate"] = _ratio(df[f"{s}_evaluations"], enrolled)
    out[f"{s}_noshow_ratio"] = _ratio(df[f"{s}_without_eval"], enrolled)
    out[f"{s}_failed_units"] = (enrolled - df[f"{s}_approved"]).clip(lower=0)
    # Optional attendance measure; dropped from the model if the dataset has none.
    out[f"{s}_attendance"] = df[f"{s}_attendance"]
    return out


def build_features(df: pd.DataFrame, checkpoint: str) -> pd.DataFrame:
    if checkpoint not in CHECKPOINTS:
        raise ValueError(f"checkpoint must be one of {CHECKPOINTS}")
    parts = [df[["prev_qual_grade", "admission_grade", "course"]].copy()]
    if checkpoint in ("cp1", "cp2"):
        parts.append(_semester(df, "s1"))
    if checkpoint == "cp2":
        s2 = _semester(df, "s2")
        parts.append(s2)
        trend = pd.DataFrame(index=df.index)
        trend["grade_delta"] = df["s2_grade"] - df["s1_grade"]
        trend["pass_rate_delta"] = s2["s2_pass_rate"] - parts[1]["s1_pass_rate"]
        trend["total_failed_units"] = s2["s2_failed_units"] + parts[1]["s1_failed_units"]
        parts.append(trend)
    X = pd.concat(parts, axis=1)
    X["course"] = X["course"].astype(str)
    return X


def feature_columns(checkpoint: str) -> Dict[str, List[str]]:
    """Numeric and categorical column names for a checkpoint."""
    sample = pd.DataFrame(
        {c: [1.0] for c in [
            "prev_qual_grade", "admission_grade",
            *[f"{s}_{k}" for s in ("s1", "s2") for k in
              ("credited", "enrolled", "evaluations", "approved", "grade", "without_eval", "attendance")],
        ]}
    )
    sample["course"] = ["0"]
    cols = list(build_features(sample, checkpoint).columns)
    return {"numeric": [c for c in cols if c not in CATEGORICAL], "categorical": CATEGORICAL}


# Groups used for per-student explanations: each group is switched off together.
def explanation_groups(checkpoint: str) -> Dict[str, List[str]]:
    groups = {
        "prior_grades": ["prev_qual_grade", "admission_grade"],
        "course": ["course"],
    }
    for s, label in (("s1", "sem1"), ("s2", "sem2")):
        if checkpoint == "cp0" or (s == "s2" and checkpoint != "cp2"):
            continue
        groups[f"{label}_pass_rate"] = [f"{s}_pass_rate", f"{s}_approved", f"{s}_failed_units"]
        groups[f"{label}_exam_attendance"] = [f"{s}_attempt_rate", f"{s}_noshow_ratio"]
        groups[f"{label}_grade"] = [f"{s}_grade", f"{s}_no_grade"]
        groups[f"{label}_load"] = [f"{s}_enrolled", f"{s}_credited", f"{s}_no_units"]
        groups[f"{label}_attendance"] = [f"{s}_attendance"]
    if checkpoint == "cp2":
        groups["trend"] = ["grade_delta", "pass_rate_delta", "total_failed_units"]
    return groups


GROUP_TEXT = {
    "prior_grades": "grades before admission",
    "course": "course",
    "sem1_pass_rate": "subjects passed in semester 1",
    "sem1_exam_attendance": "exams taken in semester 1",
    "sem1_grade": "semester 1 average grade",
    "sem1_load": "semester 1 subject load",
    "sem1_attendance": "attendance in semester 1",
    "sem2_pass_rate": "subjects passed in semester 2",
    "sem2_exam_attendance": "exams taken in semester 2",
    "sem2_grade": "semester 2 average grade",
    "sem2_load": "semester 2 subject load",
    "sem2_attendance": "attendance in semester 2",
    "trend": "change from semester 1 to semester 2",
}
