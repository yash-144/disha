"""Canonical, level-agnostic input schema for the rolling risk model.

The backend feeds these six tables from any ERP: school, UG year 1-4 or PG.
All marks are percentages 0-100. Every `day` is a day number relative to the
start of the term (day 0 = term start; negative = before the term).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

PROGRAM_LEVELS = ("school", "ug", "pg")
# Demographics kept ONLY for fairness audits; never used as model inputs.
AUDIT_COLUMNS = ["gender", "region", "imd_band", "disability", "age_band"]
FINAL_BAD = ("fail", "withdrawn")  # outcomes that count as at_risk

# table -> (required columns, optional columns). Optional ones may be missing or empty.
TABLES: Dict[str, tuple] = {
    "students": (["student_id"], ["program_level", "year_of_study", "tenth_pct", "twelfth_pct",
                                  "entrance_pct", "prior_education_ord"] + AUDIT_COLUMNS),
    "enrolments": (["student_id", "term_id", "course_id", "term_length_days"],
                   ["term_start", "outcome", "prev_attempts", "credit_load"]),
    "assessments": (["assessment_id", "course_id", "term_id", "due_day"], ["weight", "type"]),
    "results": (["student_id", "assessment_id", "submitted_day"], ["score_pct"]),
    "activity": (["student_id", "course_id", "term_id", "day", "count"], []),
    "withdrawals": (["student_id", "course_id", "term_id", "day"], []),
}
OPTIONAL_TABLES = ("students", "results", "activity", "withdrawals")
STR_COLS = ["student_id", "term_id", "course_id", "assessment_id"]
PCT_COLS = ["tenth_pct", "twelfth_pct", "entrance_pct", "score_pct"]
NUM_COLS = ["year_of_study", "prior_education_ord", "term_length_days", "prev_attempts", "credit_load",
            "due_day", "weight", "submitted_day", "day", "count"] + PCT_COLS


def validate(tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Check required columns, coerce types, reject out-of-range marks. Returns a clean copy."""
    out: Dict[str, pd.DataFrame] = {}
    for name, (req, opt) in TABLES.items():
        df = tables.get(name)
        if df is None:
            if name not in OPTIONAL_TABLES:
                raise ValueError(f"missing table: {name}")
            df = pd.DataFrame(columns=req)
        miss = [c for c in req if c not in df.columns]
        if miss:
            raise ValueError(f"table {name}: missing columns {miss}")
        df = df[[c for c in req + opt if c in df.columns]].copy()
        for c in opt:
            if c not in df.columns:
                df[c] = np.nan
        for c in df.columns:
            if c in STR_COLS:
                df[c] = df[c].astype(str)
            elif c in NUM_COLS:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in PCT_COLS:
            if c in df.columns and ((df[c] < 0) | (df[c] > 100)).any():
                raise ValueError(f"table {name}: {c} must be a percentage 0-100")
        out[name] = df.reset_index(drop=True)
    lv = out["students"]["program_level"].dropna()
    if (~lv.isin(PROGRAM_LEVELS)).any():
        raise ValueError(f"program_level must be one of {PROGRAM_LEVELS}")
    if out["enrolments"].duplicated(["student_id", "course_id", "term_id"]).any():
        raise ValueError("enrolments: duplicate (student_id, course_id, term_id)")
    if out["enrolments"]["term_length_days"].isna().any():
        raise ValueError("enrolments: term_length_days is required")
    return out


def save_tables(tables: Dict[str, pd.DataFrame], folder) -> List[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, df in tables.items():
        p = folder / f"{name}.csv.gz"
        df.to_csv(p, index=False)
        paths.append(p)
    return paths


def load_tables(folder) -> Dict[str, pd.DataFrame]:
    """Read `<table>.csv` or `<table>.csv.gz` from a folder, then validate."""
    folder = Path(folder)
    tables = {}
    for name in TABLES:
        for ext in (".csv.gz", ".csv"):
            if (folder / f"{name}{ext}").exists():
                tables[name] = pd.read_csv(folder / f"{name}{ext}", dtype=str if name != "activity" else None)
                break
    return validate(tables)
