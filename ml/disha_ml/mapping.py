"""Create a mapping-file template for your own dataset.

    python -m disha_ml.mapping --data my_students.csv --out mapping.json

It matches headers it recognises, lists every header in your file, guesses
how your outcome values map to Dropout / Graduate / Enrolled, and writes a JSON
file for you to complete. Fill in each null you have data for, check the
guesses, set grade_scale, then pass the file with --mapping to train/score.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import COLUMN_ALIASES, CORE_REQUIRED, DEFAULT_GRADE_SCALE, read_csv, resolve_columns

DESCRIPTIONS = {
    "prev_qual_grade": "Grade before university (e.g. class 12 %)",
    "admission_grade": "Admission / entrance score",
    "course": "Programme or branch",
    "s1_enrolled": "Semester 1: subjects registered (REQUIRED)",
    "s1_approved": "Semester 1: subjects passed (REQUIRED)",
    "s1_evaluations": "Semester 1: exams appeared",
    "s1_without_eval": "Semester 1: subjects with no exam taken / absent",
    "s1_grade": "Semester 1: average grade or SGPA",
    "s1_credited": "Semester 1: subjects credited by transfer/exemption",
    "s2_enrolled": "Semester 2: subjects registered",
    "s2_approved": "Semester 2: subjects passed",
    "s2_evaluations": "Semester 2: exams appeared",
    "s2_without_eval": "Semester 2: subjects with no exam taken",
    "s2_grade": "Semester 2: average grade or SGPA",
    "s2_credited": "Semester 2: subjects credited",
    "gender": "AUDIT ONLY (never a model input)",
    "age_at_enrollment": "AUDIT ONLY",
    "displaced": "AUDIT ONLY",
    "special_needs": "AUDIT ONLY",
    "target": "Final outcome column (REQUIRED for training)",
}


def _guess_outcome(value: str):
    v = value.strip().lower()
    if any(k in v for k in ("drop", "left", "discontinu", "withdraw", "detain")):
        return "Dropout"
    if any(k in v for k in ("grad", "complete", "passed out", "pass out")):
        return "Graduate"
    if any(k in v for k in ("enrol", "continu", "ongoing", "active", "repeat")):
        return "Enrolled"
    return None


def build_template(data_path: str) -> dict:
    raw = read_csv(data_path)
    resolved = resolve_columns(raw.columns)
    target_values = {}
    if resolved["target"] is not None:
        for v in sorted(raw[resolved["target"]].astype(str).str.strip().unique())[:50]:
            target_values[v] = _guess_outcome(v)
    return {
        "_help": {k: DESCRIPTIONS[k] for k in COLUMN_ALIASES},
        "_headers_in_your_file": [str(c) for c in raw.columns],
        "columns": resolved,
        "target_values": target_values,
        "grade_scale": DEFAULT_GRADE_SCALE,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Write a mapping template for your dataset.")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="mapping.json")
    a = ap.parse_args(argv)
    tpl = build_template(a.data)
    Path(a.out).write_text(json.dumps(tpl, indent=2))
    cols = tpl["columns"]
    print(f"Wrote {a.out}")
    print(f"Matched automatically: {[k for k, v in cols.items() if v]}")
    print(f"Still null (fill in if you have them): {[k for k, v in cols.items() if not v]}")
    need = [k for k in CORE_REQUIRED + ['target'] if not cols[k]]
    if need:
        print(f"REQUIRED and not yet mapped: {need}")
    if tpl["target_values"]:
        print(f"Outcome guesses (check them): {tpl['target_values']}")
    print("Set grade_scale to your semester grade maximum (10 for SGPA, 100 for percent).")


if __name__ == "__main__":
    main()
