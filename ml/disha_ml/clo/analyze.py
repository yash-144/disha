"""CO (course learning outcome) insights: which outcomes and topics students struggle with,
and whether that is a teaching gap or a student gap.

Deterministic and traceable (no ML): every number comes from question-wise marks that colleges
already keep for NBA/NAAC. The JSON schema is the dataclasses below
(see docs/architecture/CLO_SPEC.md).

    python -m disha_ml.clo.analyze --tables <dir> --course CS201 --term 2026-odd [--no-meko]

Library use:
    payload = analyze_course(tables, "CS201", "2026-odd")      # tables: dict of DataFrames or a folder
"""
from __future__ import annotations

import argparse
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from .. import meko_hooks
from ..rolling.insights import _clean
from ..rolling.schema import load_tables, validate
from .config import CloConfig

SCHEMA_VERSION = "1.0"
BLOOM = {1: "remember", 2: "understand", 3: "apply", 4: "analyse", 5: "evaluate", 6: "create"}
EPS = 1e-9


# ---- output schema ---------------------------------------------------------
@dataclass
class CoAttainment:
    co_id: str
    description: str
    target_pct: float
    n_students: int
    attainment_pct: Optional[float]      # share of students at/above the target (combined CIE + SEE)
    level: Optional[int]                 # 0-3
    mean_pct: Optional[float]
    by_kind: Dict[str, Optional[float]]  # attainment per internal / end_sem
    p_top: Optional[float]               # mean CO score (0-1) of the top group
    p_bottom: Optional[float]
    gap_type: str                        # teaching_gap | student_gap | ok | insufficient_data
    questions: List[str]
    weak_questions: List[str]            # questions of this CO whose own gap_type is not ok


@dataclass
class ItemStat:
    question_id: str
    assessment_id: str
    co_id: str
    bloom_level: Optional[int]
    type: str
    max_marks: float
    n: int
    difficulty_p: float                  # mean(marks / max)
    p_top: Optional[float]
    p_bottom: Optional[float]
    discrimination: Optional[float]      # p_top - p_bottom
    gap_type: str
    flag: Optional[str]                  # negative_discrimination | low_discrimination (possibly ambiguous)


@dataclass
class BloomCell:
    co_id: str
    bloom_level: int
    bloom_name: str
    n_students: int
    attainment_pct: Optional[float]


@dataclass
class BloomInsight:
    co_id: str
    low_pct: float
    high_pct: float
    text: str


@dataclass
class Misconception:
    question_id: str
    co_id: str
    correct_option: str
    option: str                          # the most common wrong option
    share_pct: float
    n_answered: int
    flagged: bool                        # share >= misconception_share
    top_pct: Optional[float]             # share of the top / bottom group choosing it
    bottom_pct: Optional[float]


@dataclass
class TrendPoint:
    assessment_id: str
    due_day: int
    kind: str
    attainment_pct: float
    n_students: int


@dataclass
class CoTrend:
    co_id: str
    points: List[TrendPoint]
    status: str                          # improving | declining | steady | single_point
    delta_pts: Optional[float]


@dataclass
class SectionCo:
    section: str
    n_students: int
    attainment_pct: float
    level: int
    trend: str
    delta_pts: Optional[float]


@dataclass
class SectionComparison:
    co_id: str
    sections: List[SectionCo]
    insight: Optional[str]


@dataclass
class Muddiest:
    key: str                             # co_id or free-text topic
    label: str
    n_students: int


@dataclass
class Learning:
    co_id: str
    section: Optional[str]
    action: str
    day: int
    before_pct: float
    after_pct: float
    before_level: int
    after_level: int
    improved: bool                       # level went up


@dataclass
class Recommendation:
    code: str                            # RETEACH | REMEDIAL | MISCONCEPTION | BLOOM | DECLINING | AMBIGUOUS_ITEM | SECTION | MUDDIEST | RECURRING | WORKED
    severity: str                        # high | medium | low
    co_id: Optional[str]
    text: str
    evidence: Dict[str, object] = field(default_factory=dict)


@dataclass
class StudentGap:
    student_id: str
    weakest_co: str
    weakest_co_pct: float
    n_cos_below_target: int
    weak_cos: List[Dict[str, object]]


@dataclass
class CloPayload:
    schema_version: str
    course_id: str
    term_id: str
    as_of_day: Optional[int]
    n_students: int
    sections: List[str]
    config: Dict[str, object]
    co_attainment: List[CoAttainment]
    items: List[ItemStat]
    bloom: Dict[str, object]
    misconceptions: List[Misconception]
    trends: List[CoTrend]
    section_comparison: List[SectionComparison]
    muddiest: Dict[str, object]
    learnings: List[Learning]
    recommendations: List[Recommendation]
    student_gaps: Dict[str, object]      # audience: mentor, never shown on the class view
    context: Dict[str, object]           # recalled Meko memories, verbatim
    suppressed: Dict[str, object]

    def to_dict(self) -> Dict:
        return _clean(asdict(self))

    def to_json(self, **kw) -> str:
        import json
        return json.dumps(self.to_dict(), **kw)


# ---- helpers -----------------------------------------------------------------
def level_for(att_pct: float, cuts=(70.0, 60.0, 50.0)) -> int:
    """NBA-style attainment level from the % of students reaching the target."""
    return 3 if att_pct >= cuts[0] else 2 if att_pct >= cuts[1] else 1 if att_pct >= cuts[2] else 0


def gap_type(p_top, p_bottom, cfg: CloConfig) -> str:
    """teaching_gap: even the top group struggles; student_gap: only the bottom group does."""
    if p_top is None or p_bottom is None:
        return "insufficient_data"
    if p_top < cfg.teaching_gap_p_top:
        return "teaching_gap"
    if p_top >= cfg.student_gap_p_top and p_bottom < cfg.student_gap_p_bottom:
        return "student_gap"
    return "ok"


def _kind(atype, cfg: CloConfig) -> str:
    s = str(atype).lower() if pd.notna(atype) else ""
    return "end_sem" if any(k in s for k in cfg.end_sem_keywords) else "internal"


def _nat(s: str):
    return (len(s), s)


def _pct(x) -> Optional[float]:
    return None if x is None or pd.isna(x) else round(float(x), 1)


def _long(t: Dict[str, pd.DataFrame], course: str, term: str, cfg: CloConfig, as_of) -> pd.DataFrame:
    """One row per student x question for this course-term (only assessments due by as_of)."""
    a = t["assessments"]
    a = a[(a["course_id"] == course) & (a["term_id"] == term)]
    if as_of is not None:
        a = a[a["due_day"] <= as_of]
    q = t["questions"].merge(a[["assessment_id", "due_day", "type"]].rename(columns={"type": "atype"}), on="assessment_id")
    e = t["enrolments"]
    e = e[(e["course_id"] == course) & (e["term_id"] == term)][["student_id", "section"]]
    df = t["question_results"].merge(q, on="question_id").merge(e, on="student_id")
    df["kind"] = df["atype"].map(lambda x: _kind(x, cfg))
    df["pct"] = 100 * df["marks"] / df["max_marks"]
    return df


def _targets(t, course, cfg: CloConfig, cos) -> tuple:
    """(target % per CO, description per CO)."""
    co = t["course_outcomes"]
    co = co[co["course_id"] == course].set_index("co_id")
    tg = {c: float(co["target_pct"].get(c, cfg.default_target_pct)) for c in cos}
    ds = {c: (str(co["description"].get(c)) if c in co.index and pd.notna(co["description"].get(c)) else "") for c in cos}
    return tg, ds


def _label(co, desc) -> str:
    """'CO3 (Recursion)' when a description is known."""
    return f"{co} ({desc[co]})" if desc.get(co) else co


def _co_scores(df: pd.DataFrame, cfg: CloConfig) -> pd.Series:
    """Per (student, CO) score in %, combining internal and end-sem by weight (renormalised when one is missing)."""
    g = df.groupby(["student_id", "co_id", "kind"]).agg(m=("marks", "sum"), mx=("max_marks", "sum")).reset_index()
    g["w"] = g["kind"].map(cfg.kind_weights).fillna(0.0)
    g["wp"] = 100 * g["m"] / g["mx"] * g["w"]
    s = g.groupby(["student_id", "co_id"]).agg(wp=("wp", "sum"), w=("w", "sum"))
    return (s["wp"] / s["w"]).rename("pct")


def _co_table(scores: pd.Series, targets: Dict[str, float]) -> pd.DataFrame:
    d = scores.reset_index()
    d["hit"] = d["pct"] + EPS >= d["co_id"].map(targets)
    t = d.groupby("co_id").agg(n=("hit", "size"), reached=("hit", "sum"), mean=("pct", "mean"))
    t["att"] = 100 * t["reached"] / t["n"]
    return t


def _groups(df: pd.DataFrame, cfg: CloConfig):
    """Top and bottom 27% of students by total score."""
    tot = df.groupby("student_id").agg(m=("marks", "sum"), mx=("max_marks", "sum"))
    tot["p"] = tot["m"] / tot["mx"]
    order = tot.reset_index().sort_values(["p", "student_id"])["student_id"].tolist()
    k = max(1, int(cfg.top_bottom_frac * len(order) + 0.5))
    return set(order[-k:]), set(order[:k]), k


# ---- per-student CO features (also used by the rolling model link) -----------------
def student_co_features(tables, course_id: str, term_id: str, cfg: Optional[CloConfig] = None,
                        as_of: Optional[int] = None) -> pd.DataFrame:
    """One row per student with CO data: weakest_co(_pct), n_cos_below_target, weak_cos (below target, weakest first)."""
    cfg = cfg or CloConfig()
    t = load_tables(tables) if isinstance(tables, (str, Path)) else validate(tables)
    df = _long(t, course_id, term_id, cfg, as_of)
    cols = ["student_id", "weakest_co", "weakest_co_pct", "n_cos_below_target", "weak_cos"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    cos = sorted(df["co_id"].unique(), key=_nat)
    tg, ds = _targets(t, course_id, cfg, cos)
    rows = []
    for sid, g in _co_scores(df, cfg).reset_index().groupby("student_id"):
        g = g.sort_values(["pct", "co_id"])
        weak = [{"co_id": r.co_id, "description": ds[r.co_id], "pct": round(float(r.pct), 1), "target_pct": tg[r.co_id]}
                for r in g.itertuples() if r.pct + EPS < tg[r.co_id]]
        w = g.iloc[0]
        rows.append((sid, w["co_id"], round(float(w["pct"]), 1), len(weak), weak))
    return pd.DataFrame(rows, columns=cols)


# ---- main --------------------------------------------------------------------
def analyze_course(tables: Union[Dict[str, pd.DataFrame], str, Path], course_id: str, term_id: str,
                   cfg: Optional[CloConfig] = None, as_of: Optional[int] = None, recall: bool = True) -> CloPayload:
    """CO insights for one course-term. `as_of` (day) limits the data to assessments due by then.
    `recall` pulls past-term memories from Meko into context.recalled (a no-op when Meko is off)."""
    cfg = cfg or CloConfig()
    t = load_tables(tables) if isinstance(tables, (str, Path)) else validate(tables)
    course_id, term_id = str(course_id), str(term_id)
    df = _long(t, course_id, term_id, cfg, as_of)
    n = int(df["student_id"].nunique())
    sections = sorted(df["section"].dropna().unique()) if n else []
    recalled = (meko_hooks.recall_course_history(course_id) or []) if recall else []
    ctx = {"meko": "active" if meko_hooks.is_active() else "off", "recalled": recalled}

    def empty(note):
        return CloPayload(SCHEMA_VERSION, course_id, term_id, as_of, n, sections, cfg.to_dict(), [], [],
                          {"cells": [], "insights": []}, [], [], [], {"items": [], "suppressed": 0}, [], [],
                          {"audience": "mentor", "students": []}, ctx, {"note": note})

    if n == 0:
        return empty("no question-level results for this course and term")
    if n < cfg.min_group_size:
        return empty(f"class of {n} is smaller than min_group_size={cfg.min_group_size}; class-level insights suppressed")

    cos = sorted(df["co_id"].unique(), key=_nat)
    tg, ds = _targets(t, course_id, cfg, cos)
    top, bottom, k = _groups(df, cfg)
    scores = _co_scores(df, cfg)
    tab = _co_table(scores, tg)
    sc = scores.reset_index()
    big = k >= cfg.min_group_size       # top/bottom groups large enough to show

    # item analysis
    items = []
    for qid in t["questions"]["question_id"]:
        g = df[df["question_id"] == qid]
        if g.empty:
            continue
        r = g.iloc[0]
        p = g["pct"].mean() / 100
        gt, gb = g[g["student_id"].isin(top)], g[g["student_id"].isin(bottom)]
        shown = big and len(gt) >= cfg.min_group_size and len(gb) >= cfg.min_group_size
        pt, pb = (gt["pct"].mean() / 100, gb["pct"].mean() / 100) if shown else (None, None)
        d = None if pt is None else pt - pb
        flag = None if d is None else "negative_discrimination" if d < 0 else \
            "low_discrimination" if d < cfg.low_discrimination and p < cfg.ceiling_p and gap_type(pt, pb, cfg) == "ok" else None
        items.append(ItemStat(qid, r["assessment_id"], r["co_id"], None if pd.isna(r["bloom_level"]) else int(r["bloom_level"]),
                              r["type"], float(r["max_marks"]), len(g), round(p, 3), _r3(pt), _r3(pb), _r3(d),
                              gap_type(pt, pb, cfg), flag))

    # CO attainment + gap type rolled up from student-level CO scores
    co_out = []
    for co in cos:
        row = tab.loc[co]
        pt = sc[(sc["co_id"] == co) & sc["student_id"].isin(top)]["pct"]
        pb = sc[(sc["co_id"] == co) & sc["student_id"].isin(bottom)]["pct"]
        ok = big and len(pt) >= cfg.min_group_size and len(pb) >= cfg.min_group_size
        ptv, pbv = (pt.mean() / 100, pb.mean() / 100) if ok else (None, None)
        by_kind = {}
        for kd in cfg.kind_weights:
            sub = df[(df["kind"] == kd) & (df["co_id"] == co)]
            tk = _co_table(_co_scores(sub, cfg), tg) if not sub.empty else None
            by_kind[kd] = _pct(tk.loc[co, "att"]) if tk is not None and tk.loc[co, "n"] >= cfg.min_group_size else None
        att = float(row["att"])
        qs = [i for i in items if i.co_id == co]
        co_out.append(CoAttainment(co, ds[co], tg[co], int(row["n"]), _pct(att), level_for(att, cfg.level_cuts),
                                   _pct(row["mean"]), by_kind, _r3(ptv), _r3(pbv), gap_type(ptv, pbv, cfg),
                                   [i.question_id for i in qs], [i.question_id for i in qs if i.gap_type in ("teaching_gap", "student_gap")]))
    co_map = {c.co_id: c for c in co_out}

    bloom = _bloom(df, cos, tg, cfg)
    miscon = _misconceptions(df, top, bottom, big, cfg)
    trends = _trends(df, cos, tg, cfg)
    sect, hidden_sections = _sections(df, cos, tg, cfg, t, course_id, term_id)
    mud = _muddiest(t, course_id, term_id, ds, cfg)
    learn = _learnings(df, t, course_id, term_id, cos, tg, cfg)
    gaps = student_co_features(t, course_id, term_id, cfg, as_of)
    student_gaps = {"audience": "mentor", "students": [
        asdict(StudentGap(r.student_id, r.weakest_co, r.weakest_co_pct, r.n_cos_below_target, r.weak_cos))
        for r in gaps[gaps["n_cos_below_target"] > 0].sort_values(["weakest_co_pct", "student_id"]).itertuples()]}
    recs = _recommendations(co_out, items, miscon, bloom, trends, sect, mud, learn, sc, ds, cfg, recalled, course_id, term_id)
    return CloPayload(SCHEMA_VERSION, course_id, term_id, as_of, n, sections, cfg.to_dict(), co_out, items, bloom, miscon,
                      trends, sect, mud, learn, recs, student_gaps, ctx,
                      {"min_group_size": cfg.min_group_size, "sections_hidden": hidden_sections,
                       "muddiest_hidden": mud["suppressed"]})


def _r3(x):
    return None if x is None or pd.isna(x) else round(float(x), 3)


# ---- Bloom -----------------------------------------------------------------------
def _band_att(sub: pd.DataFrame, co: str, tg, cfg):
    """(attainment %, n students) for one CO within a subset of questions."""
    if sub.empty:
        return None, 0
    tb = _co_table(_co_scores(sub, cfg), tg)
    n = int(tb.loc[co, "n"])
    return (float(tb.loc[co, "att"]) if n >= cfg.min_group_size else None), n


def _bloom(df, cos, tg, cfg) -> Dict:
    cells, insights = [], []
    d = df[df["bloom_level"].notna()]
    for co in cos:
        dc = d[d["co_id"] == co]
        for lv in sorted(dc["bloom_level"].unique()):
            att, nn = _band_att(dc[dc["bloom_level"] == lv], co, tg, cfg)
            cells.append(BloomCell(co, int(lv), BLOOM[int(lv)], nn, _pct(att)))
        lo, hi = dc[dc["bloom_level"] <= cfg.bloom_low_max], dc[dc["bloom_level"] > cfg.bloom_low_max]
        (la, _), (ha, _) = _band_att(lo, co, tg, cfg), _band_att(hi, co, tg, cfg)
        if la is not None and ha is not None and la - ha >= cfg.bloom_gap_pts and ha < cfg.level_cuts[1]:
            names = lambda x: "/".join(BLOOM[int(v)] for v in sorted(x["bloom_level"].unique()))  # noqa: E731
            insights.append(BloomInsight(co, round(la, 1), round(ha, 1),
                                         f"{co}: fine on {names(lo)} ({la:.0f}% reach the target), "
                                         f"weak on {names(hi)} ({ha:.0f}%)"))
    return {"levels": BLOOM, "cells": cells, "insights": insights}


# ---- MCQ misconceptions ---------------------------------------------------------------
def _misconceptions(df, top, bottom, big, cfg) -> List[Misconception]:
    out = []
    m = df[(df["type"] == "mcq") & df["selected_option"].notna() & df["correct_option"].notna()]
    for qid, g in m.groupby("question_id", sort=False):
        if len(g) < cfg.min_group_size:
            continue
        wrong = g[g["selected_option"] != g["correct_option"]]["selected_option"].value_counts()
        if wrong.empty:
            continue
        opt = sorted(wrong[wrong == wrong.max()].index)[0]   # ties: alphabetical, so output is stable
        share = 100 * wrong.max() / len(g)

        def grp(ids):
            s = g[g["student_id"].isin(ids)]
            return _pct(100 * (s["selected_option"] == opt).mean()) if big and len(s) >= cfg.min_group_size else None

        out.append(Misconception(qid, g["co_id"].iloc[0], g["correct_option"].iloc[0], opt, round(share, 1), len(g),
                                 bool(share + EPS >= 100 * cfg.misconception_share), grp(top), grp(bottom)))
    return sorted(out, key=lambda x: -x.share_pct)


# ---- trend over assessments --------------------------------------------------------------
def _status(points, cfg):
    if len(points) < 2:
        return "single_point", None
    d = points[-1].attainment_pct - points[0].attainment_pct
    return ("improving" if d >= cfg.trend_delta_pts else "declining" if d <= -cfg.trend_delta_pts else "steady"), round(d, 1)


def _points(df, co, tg, cfg) -> List[TrendPoint]:
    pts = []
    for aid, g in df[df["co_id"] == co].groupby("assessment_id"):
        att, nn = _band_att(g, co, tg, cfg)
        if att is not None:
            pts.append(TrendPoint(aid, int(g["due_day"].iloc[0]), g["kind"].iloc[0], round(att, 1), nn))
    return sorted(pts, key=lambda p: (p.due_day, p.assessment_id))


def _trends(df, cos, tg, cfg) -> List[CoTrend]:
    out = []
    for co in cos:
        pts = _points(df, co, tg, cfg)
        st, d = _status(pts, cfg)
        out.append(CoTrend(co, pts, st, d))
    return out


# ---- sections ----------------------------------------------------------------------------
def _sections(df, cos, tg, cfg, t, course, term):
    secs = sorted(df["section"].dropna().unique())
    if len(secs) < 2:
        return [], 0
    acts = t["teaching_actions"]
    acts = acts[(acts["course_id"] == course) & (acts["term_id"] == term)]
    shown = [s for s in secs if df[df["section"] == s]["student_id"].nunique() >= cfg.min_group_size]
    out = []
    for co in cos:
        rows = []
        for s in shown:
            sub = df[df["section"] == s]
            att, nn = _band_att(sub[sub["co_id"] == co], co, tg, cfg)
            if att is None:
                continue
            st, d = _status(_points(sub, co, tg, cfg), cfg)
            rows.append(SectionCo(s, nn, round(att, 1), level_for(att, cfg.level_cuts), st, d))
        text = None
        if len(rows) >= 2:
            best, worst = max(rows, key=lambda r: r.attainment_pct), min(rows, key=lambda r: r.attainment_pct)
            if best.attainment_pct - worst.attainment_pct >= cfg.section_gap_pts:
                a = acts[(acts["co_id"] == co) & (acts["section"] == best.section)]
                how = f" (recorded action there: {a.iloc[0]['action']} on day {int(a.iloc[0]['day'])})" if len(a) and pd.notna(a.iloc[0]["action"]) else ""
                text = (f"{co}: {best.attainment_pct:.0f}% of section {best.section} reached the target vs "
                        f"{worst.attainment_pct:.0f}% in section {worst.section}. See what worked in section {best.section}{how}.")
        out.append(SectionComparison(co, rows, text))
    return out, len(secs) - len(shown)


# ---- muddiest point ----------------------------------------------------------------------
def _muddiest(t, course, term, ds, cfg) -> Dict:
    f = t["topic_feedback"]
    f = f[(f["course_id"] == course) & (f["term_id"] == term)]
    if f.empty:
        return {"items": [], "suppressed": 0}
    f = f.assign(key=f["co_id"].fillna(f["topic"])).dropna(subset=["key"])
    cnt = f.groupby("key")["student_id"].nunique().sort_values(ascending=False)
    items = [Muddiest(k, _label(k, ds) if k in ds else k, int(v)) for k, v in cnt.items() if v >= cfg.min_group_size]
    return {"items": items, "suppressed": int((cnt < cfg.min_group_size).sum())}


# ---- teaching actions -> learnings ----------------------------------------------------------
def _learnings(df, t, course, term, cos, tg, cfg) -> List[Learning]:
    """Compare CO attainment on the last assessment before a recorded action with the first one after it."""
    a = t["teaching_actions"]
    a = a[(a["course_id"] == course) & (a["term_id"] == term)]
    out = []
    for r in a.itertuples():
        if r.co_id not in cos:
            continue
        sub = df if pd.isna(r.section) else df[df["section"] == r.section]
        pts = _points(sub, r.co_id, tg, cfg)
        before, after = [p for p in pts if p.due_day <= r.day], [p for p in pts if p.due_day > r.day]
        if not before or not after:
            continue
        b, af = before[-1], after[0]
        bl, al = level_for(b.attainment_pct, cfg.level_cuts), level_for(af.attainment_pct, cfg.level_cuts)
        out.append(Learning(r.co_id, None if pd.isna(r.section) else r.section,
                            "" if pd.isna(r.action) else r.action, int(r.day), b.attainment_pct, af.attainment_pct, bl, al, al > bl))
    return out


# ---- recommendations ---------------------------------------------------------------------------
def _recommendations(cos, items, misc, bloom, trends, sect, mud, learn, sc, ds, cfg, recalled, course, term):
    R, imap = [], {c.co_id: c for c in cos}
    byq = {i.question_id: i for i in items}
    for c in cos:
        lab = _label(c.co_id, ds)
        if c.gap_type == "teaching_gap":
            w = sorted((byq[q] for q in c.weak_questions if byq[q].gap_type == "teaching_gap"), key=lambda i: i.p_top)
            where = f"on {w[0].question_id}" if w else "on this CO"
            top = w[0].p_top if w else c.p_top
            R.append(Recommendation("RETEACH", "high" if c.level <= 1 else "medium", c.co_id,
                                    f"Re-teach {lab}: only {c.attainment_pct:.0f}% reached the target; even the top quarter "
                                    f"averaged {100 * top:.0f}% {where} — teaching gap",
                                    {"attainment_pct": c.attainment_pct, "p_top": top, "questions": [i.question_id for i in w]}))
        elif c.gap_type == "student_gap":
            low = sc[(sc["co_id"] == c.co_id) & (sc["pct"] < 100 * cfg.student_gap_p_bottom)]["student_id"].nunique()
            who = f"{low} students below {100 * cfg.student_gap_p_bottom:.0f}%" if low >= cfg.min_group_size else \
                "a small group of students is struggling (see the mentor view)"
            R.append(Recommendation("REMEDIAL", "medium", c.co_id,
                                    f"{lab}: top students are fine ({100 * c.p_top:.0f}%), {who} — schedule remedial support",
                                    {"p_top": c.p_top, "p_bottom": c.p_bottom, "n_below": low if low >= cfg.min_group_size else None}))
    for m in misc:
        if m.flagged:
            R.append(Recommendation("MISCONCEPTION", "medium", m.co_id,
                                    f"{m.question_id} ({m.co_id}): {m.share_pct:.0f}% chose option {m.option} "
                                    f"(correct: {m.correct_option}) — address this distractor",
                                    {"question_id": m.question_id, "option": m.option, "share_pct": m.share_pct}))
    for b in bloom["insights"]:
        R.append(Recommendation("BLOOM", "medium", b.co_id, f"{b.text} — add worked, applied problems", {"low_pct": b.low_pct, "high_pct": b.high_pct}))
    for tr in trends:
        if tr.status == "declining":
            R.append(Recommendation("DECLINING", "medium", tr.co_id,
                                    f"{_label(tr.co_id, ds)}: attainment fell from {tr.points[0].attainment_pct:.0f}% to "
                                    f"{tr.points[-1].attainment_pct:.0f}% across assessments — check what changed",
                                    {"delta_pts": tr.delta_pts}))
    for i in items:
        if i.flag:
            R.append(Recommendation("AMBIGUOUS_ITEM", "low", i.co_id,
                                    f"{i.question_id} may be ambiguous ({i.flag.replace('_', ' ')}, D={i.discrimination:.2f}) "
                                    "— check its wording and key", {"question_id": i.question_id, "d": i.discrimination}))
    for s in sect:
        if s.insight:
            R.append(Recommendation("SECTION", "low", s.co_id, s.insight, {}))
    for m in mud["items"][:3]:
        R.append(Recommendation("MUDDIEST", "low", m.key if m.key in imap else None,
                                f"{m.n_students} students named {m.label} as their muddiest point", {"n_students": m.n_students}))
    for l in learn:
        if l.improved:
            where = f"section {l.section}" if l.section else "the class"
            R.append(Recommendation("WORKED", "low", l.co_id,
                                    f"{l.co_id} in {where}: {l.action or 'the recorded teaching action'} on day {l.day} was followed by "
                                    f"attainment {l.before_pct:.0f}% → {l.after_pct:.0f}% (level {l.before_level} → {l.after_level})",
                                    {"action": l.action}))
    for co, terms in _recurring(recalled, course, term, {c.co_id for c in cos if c.level <= 1}).items():
        R.append(Recommendation("RECURRING", "high", co,
                                f"{_label(co, ds)} was also at level 0-1 in {', '.join(terms)} (recalled from Meko) — "
                                "a repeat problem, review the plan for this topic", {"terms": terms}))
    order = {"high": 0, "medium": 1, "low": 2}
    R.sort(key=lambda r: (order[r.severity], r.co_id or "~"))
    return R[:cfg.max_recommendations]


def _recurring(recalled, course, term, weak) -> Dict[str, List[str]]:
    """COs weak now that past-term memories also recorded at level 0-1."""
    out: Dict[str, set] = {}
    for r in recalled:
        m = meko_hooks.parse_course_summary(r.get("text", ""))
        if m and m["course"] == course and m["term"] != term:
            for co, lv in m["levels"].items():
                if co in weak and lv <= 1:
                    out.setdefault(co, set()).add(m["term"])
    return {k: sorted(v) for k, v in sorted(out.items())}


# ---- CLI ---------------------------------------------------------------------------------
def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="CO insights for one course-term; prints JSON")
    ap.add_argument("--tables", required=True, help="folder with the canonical tables (.csv or .csv.gz)")
    ap.add_argument("--course", required=True)
    ap.add_argument("--term", required=True)
    ap.add_argument("--as-of", type=int, default=None, help="only assessments due by this day")
    ap.add_argument("--out", default=None, help="write JSON here instead of stdout")
    ap.add_argument("--no-meko", action="store_true", help="never talk to Meko")
    a = ap.parse_args(argv)
    if a.no_meko:
        meko_hooks.disable()
    payload = analyze_course(a.tables, a.course, a.term, as_of=a.as_of)
    text = payload.to_json(indent=1)
    if a.out:
        Path(a.out).write_text(text)
        print(f"{payload.n_students} students analysed -> {a.out}")
    else:
        print(text)
    meko_hooks.record_course_learnings(payload.to_dict())


if __name__ == "__main__":
    main()
