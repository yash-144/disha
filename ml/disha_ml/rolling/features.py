"""Snapshots and features for the rolling risk model.

A snapshot is one row per (student, course, term, day t). Rows are built at every
assessment due date (when marks reach the ERP) and at fixed fractions of the term.
Every feature at day t uses only data dated <= t (see `cohort_features`, which
truncates its inputs first), and enrolments withdrawn at or before t get no row.
Cohort-relative values are computed within the same course and term.
"""
from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

import numpy as np
import pandas as pd

from .config import RECENT_DAYS, RULES
from .schema import FINAL_BAD

FEATURES: List[str] = [
    # scores
    "mean_score", "weighted_score", "last_score", "score_change", "score_slope",
    # standing in the cohort
    "standing_pct", "gap_to_median",
    # submissions
    "share_submitted", "n_missed", "n_late", "consecutive_misses", "missed_last3",
    # engagement
    "activity_vs_median", "engagement_ratio", "days_since_activity",
    # progress
    "term_frac", "assessment_idx",
    # baseline
    "baseline_rank", "baseline_gap", "prev_attempts", "credit_load",
    # context
    "program_level_code", "year_of_study",
]
# Feature groups for the ablation-based reasons (progress features are never a reason).
GROUPS: Dict[str, List[str]] = {
    "score_level": ["mean_score", "weighted_score", "last_score", "standing_pct", "gap_to_median"],
    "score_trend": ["score_change", "score_slope"],
    "submissions": ["share_submitted", "n_missed", "n_late", "consecutive_misses", "missed_last3"],
    "engagement": ["activity_vs_median", "engagement_ratio", "days_since_activity"],
    "baseline": ["baseline_rank", "baseline_gap"],
    "load_history": ["prev_attempts", "credit_load", "program_level_code", "year_of_study"],
}
AUX = ["n_scored", "n_due", "class_median_score", "last_assessment_id", "last_assessment",
       "next_due_day", "next_assessment_id"]
LEVEL_CODE = {"school": 0, "ug": 1, "pg": 2}


class Cohort(NamedTuple):
    course: str
    term: str
    length: float
    enrol: pd.DataFrame
    assess: pd.DataFrame
    results: pd.DataFrame
    activity: pd.DataFrame
    withdr: pd.DataFrame


def split_cohorts(tables: Dict[str, pd.DataFrame]) -> Dict[Tuple[str, str], Cohort]:
    """One Cohort (all data of one course in one term) per (course_id, term_id)."""
    key = ["course_id", "term_id"]
    en = tables["enrolments"].merge(tables["students"], on="student_id", how="left")
    asm = tables["assessments"].dropna(subset=["due_day"]).copy()
    asm["type"] = asm["type"].fillna("")
    asm = asm.sort_values(["due_day", "assessment_id"])
    # Label like TMA3: the n-th assessment of that type in the course and term.
    asm["label"] = asm["type"].where(asm["type"] != "", "A") + (asm.groupby(key + ["type"]).cumcount() + 1).astype(str)
    res = tables["results"].merge(asm[["assessment_id"] + key], on="assessment_id", how="inner")
    parts = {n: dict(tuple(df.groupby(key))) for n, df in
             [("a", asm), ("r", res), ("v", tables["activity"]), ("w", tables["withdrawals"])]}
    empty = {"a": asm.iloc[0:0], "r": res.iloc[0:0], "v": tables["activity"].iloc[0:0],
             "w": tables["withdrawals"].iloc[0:0]}
    out = {}
    for k, e in en.groupby(key):
        g = lambda n: parts[n].get(k, empty[n])  # noqa: E731
        out[k] = Cohort(k[0], k[1], float(e["term_length_days"].max()), e, g("a"), g("r"), g("v"), g("w"))
    return out


def snapshot_times(c: Cohort, fixed_fracs=(), as_of: Optional[float] = None) -> Dict[int, Dict]:
    """Days to build rows for: non-exam due dates and fixed fractions (<= as_of when given)."""
    times: Dict[int, Dict] = {}
    for d in c.assess.loc[c.assess["type"].str.lower() != "exam", "due_day"]:
        if 0 <= d <= c.length:
            times.setdefault(int(d), {})["assessment"] = True
    for f in fixed_fracs:
        times.setdefault(int(round(f * c.length)), {})["frac_tag"] = f
    if as_of is not None:
        times = {t: v for t, v in times.items() if t < as_of}
        times.setdefault(int(as_of), {})["as_of"] = True
    return times


def _matrices(c: Cohort, ids: np.ndarray, t: float):
    """Assessments due by t and student x assessment matrices of what was submitted by t."""
    A = c.assess[c.assess["due_day"] <= t]
    R = c.results[(c.results["submitted_day"] <= t) & c.results["assessment_id"].isin(A["assessment_id"])]
    R = R.drop_duplicates(["student_id", "assessment_id"])
    aidx = pd.Index(A["assessment_id"])
    r, a = pd.Index(ids).get_indexer(R["student_id"]), aidx.get_indexer(R["assessment_id"])
    ok = r >= 0
    r, a, R = r[ok], a[ok], R[ok]
    shape = (len(ids), len(A))
    sub, late, score = np.zeros(shape, bool), np.zeros(shape, bool), np.full(shape, np.nan)
    sub[r, a] = True
    late[r, a] = R["submitted_day"].to_numpy() > A["due_day"].to_numpy()[a]
    score[r, a] = R["score_pct"].to_numpy()
    return A, sub, late, score


def _score_features(A, sub, late, score) -> Dict[str, np.ndarray]:
    n, k = sub.shape
    nan = np.full(n, np.nan)
    f = {c: nan.copy() for c in ["mean_score", "weighted_score", "last_score", "score_change", "score_slope",
                                 "share_submitted", "missed_last3", "n_missed", "n_late", "consecutive_misses"]}
    f["n_scored"] = np.zeros(n)
    if k == 0:
        return f
    miss = ~sub
    f["share_submitted"] = sub.sum(1) / k
    f["n_missed"] = miss.sum(1).astype(float)
    f["n_late"] = (late & sub).sum(1).astype(float)
    f["consecutive_misses"] = np.cumprod(miss[:, ::-1], axis=1).sum(1).astype(float)
    f["missed_last3"] = miss[:, -3:].sum(1).astype(float)
    m = ~np.isnan(score)
    ns = m.sum(1)
    f["n_scored"] = ns.astype(float)
    v = np.where(m, score, 0.0)
    has = ns > 0
    f["mean_score"] = np.where(has, v.sum(1) / np.maximum(ns, 1), np.nan)
    w = np.nan_to_num(A["weight"].to_numpy(dtype=float))[None, :] * m
    f["weighted_score"] = np.where(w.sum(1) > 0, (w * v).sum(1) / np.maximum(w.sum(1), 1e-9), f["mean_score"])
    cs = np.cumsum(m, axis=1)
    last = np.where(m & (cs == ns[:, None]), v, 0).sum(1)
    prev = np.where(m & (cs == (ns - 1)[:, None]), v, 0).sum(1)
    f["last_score"] = np.where(has, last, np.nan)
    f["score_change"] = np.where(ns >= 2, last - prev, np.nan)
    x = np.arange(k, dtype=float)[None, :]
    xm = (x * m).sum(1) / np.maximum(ns, 1)
    ym = v.sum(1) / np.maximum(ns, 1)
    sxx = (((x - xm[:, None]) ** 2) * m).sum(1)
    sxy = ((x - xm[:, None]) * (v - ym[:, None]) * m).sum(1)
    f["score_slope"] = np.where((ns >= 2) & (sxx > 0), sxy / np.maximum(sxx, 1e-9), np.nan)
    return f


def _activity_features(c: Cohort, ids: np.ndarray, t: float) -> Dict[str, np.ndarray]:
    act = c.activity[c.activity["day"] <= t]  # nothing after t
    s = pd.Index(ids)

    def per_student(df, how="sum"):
        g = df.groupby("student_id")["count" if how == "sum" else "day"]
        return (g.sum() if how == "sum" else g.max()).reindex(s)

    total = per_student(act).fillna(0.0).to_numpy()
    med = np.median(total) if len(total) else 0.0
    out = {"activity_vs_median": total / med if med > 0 else np.full(len(ids), np.nan)}
    out["engagement_ratio"] = np.full(len(ids), np.nan)
    if t - RECENT_DAYS + 1 >= RECENT_DAYS:  # need >= 14 earlier days to have an earlier rate
        recent = per_student(act[act["day"] > t - RECENT_DAYS]).fillna(0.0).to_numpy()
        early = per_student(act[(act["day"] >= 0) & (act["day"] <= t - RECENT_DAYS)]).fillna(0.0).to_numpy()
        rate_e = early / (t - RECENT_DAYS + 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            out["engagement_ratio"] = np.where(rate_e > 0, np.clip((recent / RECENT_DAYS) / rate_e, 0, 10), np.nan)
    out["days_since_activity"] = t - per_student(act, "max").to_numpy(dtype=float)
    return out


def cohort_features(c: Cohort, t: float, tag: Optional[Dict] = None) -> pd.DataFrame:
    """Feature rows for every enrolment still active at day t, from data dated <= t only."""
    gone = c.withdr.loc[c.withdr["day"] <= t, "student_id"]
    E = c.enrol[~c.enrol["student_id"].isin(gone)]
    ids = E["student_id"].to_numpy()
    n = len(ids)
    A, sub, late, score = _matrices(c, ids, t)
    f = _score_features(A, sub, late, score)
    f.update(_activity_features(c, ids, t))
    mean = pd.Series(f["mean_score"])
    f["standing_pct"] = (mean.rank(pct=True) * 100).to_numpy()
    median = float(mean.median()) if mean.notna().any() else np.nan
    f["gap_to_median"] = f["mean_score"] - median
    f["class_median_score"] = np.full(n, median)
    # Baseline: entry marks if the cohort has any, otherwise the ordinal prior-education level.
    marks = E[["tenth_pct", "twelfth_pct", "entrance_pct"]].mean(axis=1, skipna=True)
    base = marks if marks.notna().any() else E["prior_education_ord"]
    f["baseline_rank"] = (base.rank(pct=True) * 100).to_numpy()
    f["baseline_gap"] = f["standing_pct"] - f["baseline_rank"]
    f["term_frac"] = np.full(n, min(max(t / c.length, 0.0), 1.0))
    f["assessment_idx"] = np.full(n, float(len(A)))
    f["n_due"] = f["assessment_idx"]
    f["prev_attempts"] = E["prev_attempts"].to_numpy(dtype=float)
    f["credit_load"] = E["credit_load"].to_numpy(dtype=float)
    f["program_level_code"] = E["program_level"].map(LEVEL_CODE).to_numpy(dtype=float)
    f["year_of_study"] = E["year_of_study"].to_numpy(dtype=float)
    upcoming = c.assess[c.assess["due_day"] > t].head(1)
    f["next_due_day"] = np.full(n, upcoming["due_day"].iloc[0] if len(upcoming) else np.nan)
    f["next_assessment_id"] = np.full(n, upcoming["assessment_id"].iloc[0] if len(upcoming) else None, dtype=object)
    f["last_assessment_id"] = np.full(n, A["assessment_id"].iloc[-1] if len(A) else None, dtype=object)
    f["last_assessment"] = np.full(n, A["label"].iloc[-1] if len(A) else None, dtype=object)
    df = pd.DataFrame(f)
    df.insert(0, "student_id", ids)
    df.insert(1, "course_id", c.course)
    df.insert(2, "term_id", c.term)
    df.insert(3, "snapshot_day", float(t))
    tag = tag or {}
    df["snapshot_kind"] = "assessment" if tag.get("assessment") else ("as_of" if tag.get("as_of") else "fixed")
    df["frac_tag"] = tag.get("frac_tag", np.nan)
    if "outcome" in E:
        df["outcome"] = E["outcome"].to_numpy()
    return df


def build_snapshots(tables: Dict[str, pd.DataFrame], fixed_fracs=(), as_of: Optional[float] = None) -> pd.DataFrame:
    """All snapshot rows. With as_of: the history up to as_of plus the as_of day itself."""
    frames = []
    for c in split_cohorts(tables).values():
        for t, tag in sorted(snapshot_times(c, fixed_fracs, as_of).items()):
            frames.append(cohort_features(c, t, tag))
    df = pd.concat(frames, ignore_index=True)
    if "outcome" in df and df["outcome"].notna().any():
        df["at_risk"] = df["outcome"].astype(str).str.lower().isin(FINAL_BAD).astype(int)
    return df


def rule_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean academic rules per row (columns are rule names); their sum feeds the tier logic."""
    R = RULES
    return pd.DataFrame({
        "MISSED_LAST3": df["missed_last3"] >= R["MISSED_LAST3"],
        "BELOW_MEDIAN_PTS": df["gap_to_median"] <= R["BELOW_MEDIAN_PTS"],
        "ENGAGEMENT_RATIO": df["engagement_ratio"] <= R["ENGAGEMENT_RATIO"],
        "SCORE_DROP_PTS": df["score_change"] <= R["SCORE_DROP_PTS"],
        "BELOW_BASELINE_PTS": df["baseline_gap"] <= R["BELOW_BASELINE_PTS"],
        "CONSECUTIVE_MISSES": df["consecutive_misses"] >= R["CONSECUTIVE_MISSES"],
    }, index=df.index).fillna(False)
