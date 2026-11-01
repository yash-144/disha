"""Academic rules that produce plain-language reason codes.

Rules do two jobs:
1. Corroborate a MEDIUM model score before a signal is raised (signal.py).
2. Give staff a concrete, checkable reason ("passed 2 of 6 subjects").
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from .config import RULES


def _n(x: float) -> str:
    """Whole numbers without decimals; converted values (e.g. credits / 6) with one."""
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


def _sem_rules(row: pd.Series, s: str, label: str, th: Dict[str, float]) -> List[Dict]:
    out: List[Dict] = []
    enrolled = row.get(f"{s}_enrolled")
    if enrolled is None or pd.isna(enrolled) or enrolled <= 0:
        return out
    approved = row[f"{s}_approved"]
    no_eval = row[f"{s}_without_eval"]
    grade = row[f"{s}_grade"]
    rate = approved / enrolled
    if rate < th["LOW_PASS_RATE"]:
        out.append({"code": "LOW_PASS_RATE", "text": f"passed {_n(approved)} of {_n(enrolled)} subjects in {label}"})
    if no_eval >= th["EXAM_NO_SHOW"]:
        out.append({"code": "EXAM_NO_SHOW", "text": f"no exam taken in {_n(no_eval)} subject(s) in {label}"})
    if enrolled - approved >= th["FAILED_UNITS"]:
        out.append({"code": "FAILED_UNITS", "text": f"{_n(enrolled - approved)} subjects not passed in {label}"})
    if pd.notna(grade) and grade < th["LOW_GRADE"]:
        out.append({"code": "LOW_GRADE", "text": f"{label} average grade {grade:.1f}/20"})
    return out


def evaluate_rules(raw_row: pd.Series, checkpoint: str, thresholds: Dict[str, float] | None = None) -> List[Dict]:
    """Rules that fire for one student at a checkpoint (uses cleaned raw columns)."""
    th = {**RULES, **(thresholds or {})}
    fired: List[Dict] = []
    if checkpoint in ("cp1", "cp2"):
        fired += _sem_rules(raw_row, "s1", "semester 1", th)
    if checkpoint == "cp2":
        fired += _sem_rules(raw_row, "s2", "semester 2", th)
        g1, g2 = raw_row["s1_grade"], raw_row["s2_grade"]
        if pd.notna(g1) and pd.notna(g2) and g1 - g2 >= th["GRADE_DROP"]:
            fired.append({"code": "GRADE_DROP", "text": f"average grade fell from {g1:.1f} to {g2:.1f}"})
    return fired


def rule_count(raw: pd.DataFrame, checkpoint: str) -> pd.Series:
    """Number of rules fired per student; used as the rules-only baseline score."""
    return raw.apply(lambda r: len(evaluate_rules(r, checkpoint)), axis=1).astype(float)
