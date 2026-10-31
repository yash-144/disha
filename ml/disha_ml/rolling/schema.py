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
                   ["term_start", "outcome", "prev_attempts", "credit_load", "section"]),
    "assessments": (["assessment_id", "course_id", "term_id", "due_day"], ["weight", "type"]),
    "results": (["student_id", "assessment_id", "submitted_day"], ["score_pct"]),
    "activity": (["student_id", "course_id", "term_id", "day", "count"], []),
    "withdrawals": (["student_id", "course_id", "term_id", "day"], []),
    # Course-outcome (CLO) tables, all optional: see docs/architecture/CLO_SPEC.md
    "course_outcomes": (["course_id", "co_id"], ["description", "target_pct"]),
    "questions": (["question_id", "assessment_id", "co_id", "max_marks"], ["bloom_level", "type", "correct_option"]),
    "question_results": (["student_id", "question_id", "marks"], ["selected_option"]),
    "topic_feedback": (["student_id", "course_id", "term_id", "day"], ["co_id", "topic"]),
    "teaching_actions": (["course_id", "term_id", "co_id", "day"], ["section", "action"]),
}
CLO_TABLES = ("course_outcomes", "questions", "question_results", "topic_feedback", "teaching_actions")
OPTIONAL_TABLES = ("students", "results", "activity", "withdrawals") + CLO_TABLES
QUESTION_TYPES = ("mcq", "descriptive", "rubric")
STR_COLS = ["student_id", "term_id", "course_id", "assessment_id", "question_id"]
# Text columns where blank means "not given" (kept as NaN, not the string "nan").
OPT_STR_COLS = ["co_id", "section", "correct_option", "selected_option", "topic", "description", "action"]
PCT_COLS = ["tenth_pct", "twelfth_pct", "entrance_pct", "score_pct"]
NUM_COLS = ["year_of_study", "prior_education_ord", "term_length_days", "prev_attempts", "credit_load",
            "due_day", "weight", "submitted_day", "day", "count", "marks", "max_marks", "bloom_level",
            "target_pct"] + PCT_COLS


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
            elif c in OPT_STR_COLS:
                up = c in ("correct_option", "selected_option")
                df[c] = df[c].map(lambda v: v if pd.isna(v) else (str(v).strip().upper() if up else str(v).strip())).astype(object)
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
    _validate_clo(out)
    return out


def _validate_clo(out: Dict[str, pd.DataFrame]) -> None:
    """Extra checks for the CO tables (in place): ranges, question types, marks within max_marks."""
    co, q, qr = out["course_outcomes"], out["questions"], out["question_results"]
    if len(co):
        co["target_pct"] = co["target_pct"].fillna(60.0)
        if ((co["target_pct"] < 0) | (co["target_pct"] > 100)).any():
            raise ValueError("course_outcomes: target_pct must be a percentage 0-100")
    if len(q):
        if q["question_id"].duplicated().any():
            raise ValueError("questions: duplicate question_id")
        if (q["max_marks"].isna() | (q["max_marks"] <= 0)).any():
            raise ValueError("questions: max_marks must be > 0")
        if (q["bloom_level"].notna() & ~q["bloom_level"].isin(range(1, 7))).any():
            raise ValueError("questions: bloom_level must be 1-6")
        q["type"] = [str(t).lower() if pd.notna(t) else ("mcq" if pd.notna(o) else "descriptive")
                     for t, o in zip(q["type"], q["correct_option"])]
        if (~q["type"].isin(QUESTION_TYPES)).any():
            raise ValueError(f"questions: type must be one of {QUESTION_TYPES}")
    if len(qr):
        if (qr["marks"].isna() | (qr["marks"] < 0)).any():
            raise ValueError("question_results: marks must be >= 0")
        over = qr.merge(q[["question_id", "max_marks"]], on="question_id")
        if (over["marks"] > over["max_marks"]).any():
            raise ValueError("question_results: marks above the question's max_marks")


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
