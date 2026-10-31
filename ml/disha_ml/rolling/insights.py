"""Insights engine: turns scored snapshots into mentor-facing, traceable insights.

Everything is deterministic and computed from the canonical tables plus the model's
probabilities; the JSON schema is the dataclasses below (see docs/architecture/INSIGHTS_SPEC.md).
Reasons come from feature-group ablation (explain.group_contributions): a group is a
reason when replacing it with a typical student's values lowers the risk by >= MIN_EFFECT.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..explain import group_contributions
from .config import DELTA_STEADY, DRIFT, MIN_EFFECT, PSI_SHIFT, PSI_WATCH
from .features import FEATURES, GROUPS, Cohort, _matrices

SCHEMA_VERSION = "1.0"
TIERS = ("HIGH", "MEDIUM", "WATCH", "ON_TRACK")
NO_PSI = {"term_frac", "assessment_idx",  # progress moves with the calendar by design
          "baseline_rank"}  # a within-cohort rank (ties make its PSI spiky); baseline_gap covers it


# ---- output schema ---------------------------------------------------------
@dataclass
class Reason:
    group: str            # score_level | score_trend | submissions | engagement | baseline | load_history
    text: str
    effect_pts: float     # change in risk (percentage points) if this group looked typical; negative = protective
    values: Dict[str, Optional[float]] = field(default_factory=dict)


@dataclass
class DriftEvent:
    code: str             # SCORE_DROP | ENGAGEMENT_COLLAPSE | FIRST_MISSED_SUBMISSION
    day: int
    text: str
    values: Dict[str, Optional[float]] = field(default_factory=dict)


@dataclass
class Risk:
    probability: float
    tier: str             # HIGH | MEDIUM | WATCH | ON_TRACK
    signal: bool          # HIGH or MEDIUM, after the capacity cap
    previous_probability: Optional[float]
    previous_tier: Optional[str]
    previous_day: Optional[int]
    delta: Optional[float]
    direction: str        # up | down | steady | new


@dataclass
class NextCheck:
    day: Optional[int]
    date: Optional[str]   # ISO date when term_start is known
    assessment_id: Optional[str]


@dataclass
class HistoryPoint:
    day: int
    probability: float
    tier: str


@dataclass
class StudentInsight:
    student_id: str
    course_id: str
    term_id: str
    as_of_day: int
    last_assessment: Optional[str]
    risk: Risk
    reasons: List[Reason]
    on_track: List[Reason]
    drift_events: List[DriftEvent]
    next_check: NextCheck
    snapshot: Dict[str, Optional[float]]
    history: List[HistoryPoint]


@dataclass
class TierShare:
    n: int
    share: float


@dataclass
class Hotspot:
    assessment_id: str
    label: str
    due_day: int
    n_students: int
    share_of_at_risk: float


@dataclass
class HotspotBar:
    assessment_id: str
    label: str
    due_day: int
    n_students: int


@dataclass
class TimePoint:
    day: int
    n_active: int
    signalled_share: float            # share of enrolled students signalled at this snapshot
    cumulative_signalled_share: float  # share of enrolled students signalled at any snapshot so far


@dataclass
class CohortInsight:
    course_id: str
    term_id: str
    as_of_day: int
    n_enrolled: int
    n_active: int
    n_withdrawn: int
    tier_distribution: Dict[str, TierShare]
    at_risk_share: float              # HIGH + MEDIUM share of active students
    mean_risk: float
    hotspot: Optional[Hotspot]
    hotspot_breakdown: List[HotspotBar]
    time_to_risk: List[TimePoint]


@dataclass
class FeatureDrift:
    feature: str
    psi: float
    status: str           # ok | watch | shift


@dataclass
class DriftReport:
    reference_rows: int
    current_rows: int
    max_psi: float
    retrain_recommended: bool
    note: str
    features: List[FeatureDrift]


@dataclass
class InsightsPayload:
    schema_version: str
    as_of_day: int
    model: Dict[str, object]
    n_students: int
    students: List[StudentInsight]
    cohorts: List[CohortInsight]
    data_drift: DriftReport

    def to_dict(self) -> Dict:
        return _clean(asdict(self))

    def to_json(self, **kw) -> str:
        import json
        return json.dumps(self.to_dict(), **kw)


def _clean(o):
    """NaN/inf -> None, numpy -> python, so the result is plain JSON."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# ---- reasons -----------------------------------------------------------------
def _v(r, k) -> Optional[float]:
    x = r.get(k)
    return None if x is None or pd.isna(x) else float(x)


def _texts(group: str, r) -> tuple:
    """(risk text, protective text, values) for one feature group and one snapshot row."""
    g = {k: _v(r, k) for k in GROUPS[group]}
    if group == "score_level" and g["mean_score"] is not None:
        m, gap, sp = g["mean_score"], g["gap_to_median"], g["standing_pct"]
        risk = (f"Average {m:.0f}%, {abs(gap):.0f} points below the class median" if gap is not None and gap <= -5
                else f"Average {m:.0f}%, {sp:.0f}th percentile in the class")
        ok = (f"Average {m:.0f}%, {gap:.0f} points above the class median" if gap is not None and gap >= 5
              else f"Average {m:.0f}%, in line with the class median")
        return risk, ok, g
    if group == "score_trend" and g["score_change"] is not None:
        sc, sl = g["score_change"], g["score_slope"]
        risk = (f"Score fell {abs(sc):.0f} points since the previous assessment" if sc <= -5
                else f"Scores trending down ({sl:.1f} points per assessment)" if sl is not None and sl < 0 else None)
        ok = (f"Score rose {sc:.0f} points since the previous assessment" if sc >= 5
              else "Scores steady or rising" if sl is not None and sl >= 0 else None)
        return risk, ok, g
    if group == "submissions" and g["share_submitted"] is not None:
        due, miss, last3, late = _v(r, "n_due"), g["n_missed"], g["missed_last3"], g["n_late"]
        risk = (f"Missed {last3:.0f} of the last {min(3, due):.0f} assessments" if last3 >= 1
                else f"Missed {miss:.0f} of {due:.0f} assessments so far" if miss >= 1
                else f"{late:.0f} of {due:.0f} assessments submitted late" if late >= 1 else None)
        ok = f"Submitted all {due:.0f} assessments so far" if miss == 0 and due >= 1 else None
        return risk, ok, g
    if group == "engagement":
        ratio, vs, since = g["engagement_ratio"], g["activity_vs_median"], g["days_since_activity"]
        risk = (f"Online activity down {100 * (1 - ratio):.0f}% over the last 2 weeks vs their own earlier rate"
                if ratio is not None and ratio <= 0.7
                else f"Online activity at {100 * vs:.0f}% of the class median" if vs is not None and vs <= 0.6
                else f"No online activity for {since:.0f} days" if since is not None and since >= 14 else None)
        ok = (f"Online activity at {100 * vs:.0f}% of the class median" if vs is not None and vs >= 1.0
              else None)
        return risk, ok, g
    if group == "baseline" and g["baseline_gap"] is not None:
        gap = g["baseline_gap"]
        return ("Performing below their entry baseline" if gap <= -10 else None,
                "Performing above their entry baseline" if gap >= 10 else None, g)
    if group == "load_history":
        pa, cl = g["prev_attempts"], g["credit_load"]
        risk = (f"{pa:.0f} previous attempt{'s' if pa != 1 else ''} at this course" if pa and pa >= 1
                else f"Heavy study load ({cl:.0f} credits)" if cl and cl >= 120 else None)
        return risk, None, g
    return None, None, g


def reasons_for(row, contrib: pd.Series, k: int = 3, k_ok: int = 2):
    """Top-k risk reasons and top-k protective factors for one row, from ablation effects."""
    up = contrib[contrib >= MIN_EFFECT].sort_values(ascending=False)
    down = contrib[contrib <= -MIN_EFFECT].sort_values()
    reasons, ok = [], []
    for grp, eff in up.items():
        risk, _, vals = _texts(grp, row)
        if risk:
            reasons.append(Reason(grp, risk, round(float(eff) * 100, 1), vals))
    for grp, eff in down.items():
        _, good, vals = _texts(grp, row)
        if good:
            ok.append(Reason(grp, good, round(float(eff) * 100, 1), vals))
    return reasons[:k], ok[:k_ok]


def explain(model, X: pd.DataFrame, ref: Dict) -> pd.DataFrame:
    return group_contributions(model, X, GROUPS, ref)


# ---- student drift events ------------------------------------------------------
def add_previous(scored: pd.DataFrame) -> pd.DataFrame:
    """Add prev_* columns (the same enrolment's previous snapshot) to a scored history."""
    df = scored.sort_values(["course_id", "term_id", "student_id", "snapshot_day"]).copy()
    g = df.groupby(["course_id", "term_id", "student_id"], sort=False)
    for c in ("p", "tier", "snapshot_day", "n_missed", "n_scored", "engagement_ratio"):
        df["prev_" + c] = g[c].shift(1)
    return df


def drift_events(r) -> List[DriftEvent]:
    day = int(r["snapshot_day"])
    out = []
    sc = _v(r, "score_change")
    if sc is not None and sc <= -DRIFT["SCORE_DROP_PTS"] and r["n_scored"] > (r["prev_n_scored"] if pd.notna(r["prev_n_scored"]) else 0):
        out.append(DriftEvent("SCORE_DROP", day, f"Score fell {abs(sc):.0f} points on {r['last_assessment']}",
                              {"score_change": sc, "last_score": _v(r, "last_score")}))
    er, pr = _v(r, "engagement_ratio"), _v(r, "prev_engagement_ratio")
    lim = DRIFT["ENGAGEMENT_COLLAPSE_RATIO"]
    if er is not None and er <= lim and (pr is None or pr > lim):
        out.append(DriftEvent("ENGAGEMENT_COLLAPSE", day,
                              f"Online activity collapsed: down {100 * (1 - er):.0f}% over the last 2 weeks vs their own earlier rate",
                              {"engagement_ratio": er}))
    pm = r["prev_n_missed"] if pd.notna(r["prev_n_missed"]) else 0
    if r["n_missed"] >= 1 and pm == 0:
        out.append(DriftEvent("FIRST_MISSED_SUBMISSION", day, f"First missed submission (by {r['last_assessment']})",
                              {"n_missed": float(r["n_missed"])}))
    return out


# ---- PSI / data drift ------------------------------------------------------------
def psi(ref, cur, bins: int = 10, eps: float = 1e-4) -> float:
    """Population Stability Index of `cur` against `ref`; missing values form their own bin."""
    ref, cur = np.asarray(ref, float), np.asarray(cur, float)
    if len(cur) == 0 or len(ref) == 0:
        return 0.0
    ok = ref[~np.isnan(ref)]
    edges = np.unique(np.quantile(ok, np.linspace(0, 1, bins + 1)[1:-1])) if len(ok) else np.array([])

    def share(x):
        miss = np.isnan(x)
        counts = np.bincount(np.digitize(x[~miss], edges), minlength=len(edges) + 1).astype(float)
        return np.clip(np.append(counts, miss.sum()) / len(x), eps, None)

    a, b = share(ref), share(cur)
    return float(((b - a) * np.log(b / a)).sum())


def drift_report(reference: pd.DataFrame, current: pd.DataFrame) -> DriftReport:
    """PSI per feature. The reference is the training cohorts at the fixed term fraction nearest to the batch."""
    if len(current) and "frac_tag" in reference:
        tags = reference["frac_tag"].dropna().unique()
        tag = min(tags, key=lambda f: abs(f - current["term_frac"].mean()))
        reference = reference[reference["frac_tag"] == tag]
    feats = []
    for f in FEATURES:
        if f in NO_PSI or f not in reference or f not in current:
            continue
        v = psi(reference[f], current[f])
        feats.append(FeatureDrift(f, round(v, 4), "shift" if v > PSI_SHIFT else "watch" if v > PSI_WATCH else "ok"))
    feats.sort(key=lambda x: -x.psi)
    mx = feats[0].psi if feats else 0.0
    shifted = [x.feature for x in feats if x.status == "shift"]
    note = (f"PSI > {PSI_SHIFT} on {', '.join(shifted)}: the scoring data differs from training data; "
            "consider retraining." if shifted else "No feature shifted beyond the PSI threshold.")
    return DriftReport(len(reference), len(current), mx, bool(shifted), note, feats)


# ---- cohort insights ----------------------------------------------------------------
def _hotspot(c: Cohort, cur: pd.DataFrame, t: float):
    """First assessment at which each currently signalled student fell behind (missed, or 10+ points under the median)."""
    ids = cur["student_id"].to_numpy()
    A, sub, _, score = _matrices(c, ids, t)
    flagged = cur["signal"].to_numpy()
    if not flagged.any() or len(A) == 0:
        return None, []
    with np.errstate(all="ignore"):
        med = np.nanmedian(score, axis=0)
    behind = ~sub | (score < med[None, :] - 10)
    first = np.where(behind.any(1), behind.argmax(1), -1)[flagged]
    counts = np.bincount(first[first >= 0], minlength=len(A))
    bars = [HotspotBar(str(A["assessment_id"].iloc[i]), str(A["label"].iloc[i]), int(A["due_day"].iloc[i]), int(counts[i]))
            for i in range(len(A))]
    if counts.max() == 0:
        return None, bars
    i = int(counts.argmax())
    return Hotspot(bars[i].assessment_id, bars[i].label, bars[i].due_day, int(counts[i]),
                   round(float(counts[i] / flagged.sum()), 3)), bars


def cohort_insight(c: Cohort, hist: pd.DataFrame, as_of: int) -> CohortInsight:
    cur = hist[hist["snapshot_day"] == as_of]
    n_act = len(cur)
    dist = {t: TierShare(int((cur["tier"] == t).sum()), round(float((cur["tier"] == t).mean()), 4) if n_act else 0.0)
            for t in TIERS}
    n_enr = len(c.enrol)
    ever, curve = set(), []
    for day, g in hist.groupby("snapshot_day"):
        sig = g[g["signal"]]
        ever |= set(sig["student_id"])
        curve.append(TimePoint(int(day), len(g), round(len(sig) / n_enr, 4), round(len(ever) / n_enr, 4)))
    hot, bars = _hotspot(c, cur, as_of) if n_act else (None, [])
    return CohortInsight(c.course, c.term, as_of, n_enr, n_act, n_enr - n_act, dist,
                         round(float(cur["signal"].mean()), 4) if n_act else 0.0,
                         round(float(cur["p"].mean()), 4) if n_act else 0.0, hot, bars, curve)


# ---- student insights -----------------------------------------------------------------
SNAP_KEYS = ["mean_score", "class_median_score", "standing_pct", "gap_to_median", "share_submitted", "n_missed",
             "activity_vs_median", "engagement_ratio", "term_frac"]


def student_insights(hist: pd.DataFrame, contrib: pd.DataFrame, cohorts: Dict, as_of: int) -> List[StudentInsight]:
    """One StudentInsight per enrolment active at as_of. `hist` must come from add_previous."""
    key = ["course_id", "term_id", "student_id"]
    series = {k: g for k, g in hist.groupby(key, sort=False)}
    out = []
    for idx, r in hist[hist["snapshot_day"] == as_of].iterrows():
        pp = None if pd.isna(r["prev_p"]) else float(r["prev_p"])
        delta = None if pp is None else float(r["p"]) - pp
        direction = "new" if pp is None else "up" if delta >= DELTA_STEADY else "down" if delta <= -DELTA_STEADY else "steady"
        risk = Risk(float(r["p"]), r["tier"], bool(r["signal"]), pp, None if pp is None else r["prev_tier"],
                    None if pp is None else int(r["prev_snapshot_day"]), delta, direction)
        reasons, ok = reasons_for(r, contrib.loc[idx])
        coh = cohorts[(r["course_id"], r["term_id"])]
        nd = None if pd.isna(r["next_due_day"]) else int(r["next_due_day"])
        start = coh.enrol["term_start"].iloc[0] if "term_start" in coh.enrol else None
        date = None if nd is None or pd.isna(pd.to_datetime(start, errors="coerce")) else \
            (pd.to_datetime(start) + pd.Timedelta(days=nd)).date().isoformat()
        h = series[(r["course_id"], r["term_id"], r["student_id"])]
        out.append(StudentInsight(
            str(r["student_id"]), r["course_id"], r["term_id"], as_of, r["last_assessment"], risk, reasons, ok,
            drift_events(r), NextCheck(nd, date, r["next_assessment_id"] if nd is not None else None),
            {k: _v(r, k) for k in SNAP_KEYS},
            [HistoryPoint(int(d), float(p), t) for d, p, t in zip(h["snapshot_day"], h["p"], h["tier"])]))
    return out
