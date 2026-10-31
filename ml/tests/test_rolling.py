"""Rolling model: causality, withdrawals, grouped splits, features, reasons, drift, PSI, schema."""
import json

import numpy as np
import pandas as pd
import pytest

from disha_ml.rolling import insights as I
from disha_ml.rolling.config import RollingConfig
from disha_ml.rolling.evaluate import ece, lead_time, tiers_per_snapshot
from disha_ml.rolling.features import FEATURES, GROUPS, build_snapshots, cohort_features, snapshot_times, split_cohorts
from disha_ml.rolling.schema import validate
from disha_ml.rolling.train import group_splits

from .rolling_fixtures import make_tables, tiny_tables


def feats(tables, t):
    c = next(iter(split_cohorts(tables).values()))
    return cohort_features(c, t).set_index("student_id")


def test_snapshot_uses_no_data_after_t():
    T = tiny_tables()
    base = feats(T, 30)[FEATURES]
    # Add late results, later activity and a later withdrawal: nothing dated <= 30 changes.
    T2 = {k: v.copy() for k, v in T.items()}
    T2["results"] = pd.concat([T2["results"], pd.DataFrame([("B", "a2", 31, 5.0), ("C", "ex", 95, 1.0)],
                                                           columns=["student_id", "assessment_id", "submitted_day", "score_pct"])])
    T2["activity"] = pd.concat([T2["activity"], pd.DataFrame({"student_id": list("ABC"), "course_id": "C", "term_id": "T",
                                                              "day": [31, 40, 50], "count": [999, 999, 999]})])
    T2["withdrawals"] = pd.concat([T2["withdrawals"], pd.DataFrame({"student_id": ["A"], "course_id": "C", "term_id": "T", "day": [31]})])
    T2["assessments"].loc[T2["assessments"].assessment_id == "ex", "weight"] = 5  # an assessment due later
    pd.testing.assert_frame_equal(base, feats(validate(T2), 30)[FEATURES])


def test_withdrawn_at_or_before_t_are_excluded():
    T = tiny_tables()
    assert "D" in feats(T, 24).index
    assert "D" not in feats(T, 25).index and "D" not in feats(T, 30).index
    snaps = build_snapshots(T, (0.1, 0.5))
    assert not ((snaps.student_id == "D") & (snaps.snapshot_day >= 25)).any()


def test_group_split_has_no_student_overlap():
    groups = np.repeat([f"s{i}" for i in range(200)], 5)   # 5 snapshot rows per student
    for tr, te in group_splits(groups, 5, seed=1):
        assert not set(groups[tr]) & set(groups[te])
    assert len(set(np.concatenate([te for _, te in group_splits(groups, 5, 1)]))) == len(groups)


def test_hand_built_features_at_day_30():
    f = feats(tiny_tables(), 30)
    assert list(f.index) == ["A", "B", "C"]
    a, b, c = f.loc["A"], f.loc["B"], f.loc["C"]
    assert (a.mean_score, a.last_score, a.score_change, a.score_slope) == (70, 60, -20, -20)
    assert a.weighted_score == 70 and a.share_submitted == 1 and a.n_missed == 0 and a.assessment_idx == 2
    assert (b.mean_score, b.share_submitted, b.n_missed, b.n_late, b.consecutive_misses, b.missed_last3) == (40, 0.5, 1, 1, 1, 1)
    assert np.isnan(b.score_change) and np.isnan(b.score_slope)
    assert c.mean_score == 90 and c.n_late == 0
    # Cohort relative: active means are 70, 40, 90 -> median 70.
    assert (a.gap_to_median, b.gap_to_median, c.gap_to_median) == (0, -30, 20)
    assert b.standing_pct == pytest.approx(100 / 3) and c.standing_pct == 100
    # Activity: totals 62, 34, 62 -> median 62. B was silent for the last 14 days (days 17-30).
    assert b.activity_vs_median == pytest.approx(34 / 62)
    assert a.engagement_ratio == pytest.approx(1.0) and b.engagement_ratio == 0
    assert b.days_since_activity == 14 and a.days_since_activity == 0
    assert a.term_frac == 0.3
    # Baseline ordinal A=3, B=1, C=2 -> ranks 100, 33, 67; standing 67, 33, 100.
    assert a.baseline_gap == pytest.approx(200 / 3 - 100) and c.baseline_gap == pytest.approx(100 - 200 / 3)
    assert b.prev_attempts == 1 and a.program_level_code == 1


def test_snapshot_times_skip_exams_and_add_fixed_points():
    c = next(iter(split_cohorts(tiny_tables()).values()))
    t = snapshot_times(c, (0.1, 0.5))
    assert sorted(t) == [10, 30, 50] and t[10] == {"assessment": True, "frac_tag": 0.1}
    t2 = snapshot_times(c, (0.1, 0.5), as_of=40)
    assert sorted(t2) == [10, 30, 40] and t2[40] == {"as_of": True}


def test_demographics_are_not_model_inputs():
    for bad in ("gender", "region", "imd_band", "disability", "age_band"):
        assert bad not in FEATURES


def test_schema_rejects_bad_marks_and_missing_columns():
    T = tiny_tables()
    bad = {k: v.copy() for k, v in T.items()}
    bad["results"].loc[0, "score_pct"] = 120
    with pytest.raises(ValueError, match="0-100"):
        validate(bad)
    with pytest.raises(ValueError, match="missing columns"):
        validate({**T, "assessments": T["assessments"].drop(columns="due_day")})
    with pytest.raises(ValueError, match="missing table"):
        validate({"students": T["students"]})


# ---- reasons, events, PSI ----------------------------------------------------------
ROW = {"mean_score": 41.0, "weighted_score": 41.0, "last_score": 30.0, "standing_pct": 10.0, "gap_to_median": -23.0,
       "score_change": -18.0, "score_slope": -9.0, "share_submitted": 0.5, "n_missed": 2.0, "n_late": 0.0,
       "consecutive_misses": 2.0, "missed_last3": 2.0, "n_due": 4.0, "activity_vs_median": 0.3, "engagement_ratio": 0.36,
       "days_since_activity": 9.0, "baseline_rank": 70.0, "baseline_gap": -45.0, "prev_attempts": 0.0, "credit_load": 60.0,
       "program_level_code": 1.0, "year_of_study": np.nan}


def test_reason_templates_have_the_numbers():
    contrib = pd.Series({"score_level": .3, "score_trend": .2, "submissions": .25, "engagement": .1, "baseline": .05, "load_history": 0.0})
    reasons, ok = I.reasons_for(ROW, contrib)
    assert [r.group for r in reasons] == ["score_level", "submissions", "score_trend"]   # top 3 by effect
    assert reasons[0].text == "Average 41%, 23 points below the class median" and reasons[0].effect_pts == 30.0
    assert reasons[1].text == "Missed 2 of the last 3 assessments"
    assert reasons[2].text == "Score fell 18 points since the previous assessment"
    assert I._texts("engagement", ROW)[0] == "Online activity down 64% over the last 2 weeks vs their own earlier rate"
    assert I._texts("baseline", ROW)[0] == "Performing below their entry baseline"
    assert ok == []


def test_protective_factors_and_missing_data():
    good = {**ROW, "mean_score": 85.0, "gap_to_median": 12.0, "n_missed": 0.0, "missed_last3": 0.0, "baseline_gap": 20.0}
    _, ok = I.reasons_for(good, pd.Series({"score_level": -.2, "submissions": -.1, "baseline": -.05, "engagement": 0.0}))
    assert ok[0].text == "Average 85%, 12 points above the class median" and len(ok) == 2
    assert ok[1].text == "Submitted all 4 assessments so far"
    empty = {k: np.nan for k in ROW}
    assert I.reasons_for(empty, pd.Series({"score_level": .5})) == ([], [])


def _event_row(**kw):
    base = {"snapshot_day": 90, "last_assessment": "TMA3", "score_change": -20.0, "last_score": 40.0, "n_scored": 3,
            "prev_n_scored": 2, "engagement_ratio": 0.3, "prev_engagement_ratio": 0.9, "n_missed": 1, "prev_n_missed": 0}
    return pd.Series({**base, **kw})


def test_drift_events():
    codes = lambda r: [e.code for e in I.drift_events(r)]  # noqa: E731
    assert codes(_event_row()) == ["SCORE_DROP", "ENGAGEMENT_COLLAPSE", "FIRST_MISSED_SUBMISSION"]
    assert I.drift_events(_event_row())[0].text == "Score fell 20 points on TMA3"
    # Small drop, no new mark, already collapsed, already missed: nothing new to report.
    quiet = _event_row(score_change=-10.0, engagement_ratio=0.3, prev_engagement_ratio=0.2, prev_n_missed=1)
    assert codes(quiet) == []
    assert "SCORE_DROP" not in codes(_event_row(prev_n_scored=3))          # same mark as last time
    assert codes(_event_row(prev_n_scored=np.nan, prev_engagement_ratio=np.nan, prev_n_missed=np.nan))[0] == "SCORE_DROP"


def test_psi():
    rng = np.random.default_rng(0)
    a = rng.normal(size=5000)
    assert I.psi(a, rng.normal(size=5000)) < 0.05
    assert I.psi(a, rng.normal(1.0, 1, size=5000)) > 0.2
    assert I.psi(a, np.full(100, np.nan)) > 0.2                             # everything missing is a shift
    assert I.psi(a, []) == 0.0
    rep = I.drift_report(pd.DataFrame({"mean_score": a, "term_frac": .5}), pd.DataFrame({"mean_score": a + 2, "term_frac": .5}))
    assert rep.retrain_recommended and "consider retraining" in rep.note and rep.features[0].status == "shift"


def test_ece_and_cap_per_snapshot():
    assert ece([0, 1, 0, 1], [0.0, 1.0, 0.0, 1.0]) == 0
    df = pd.DataFrame({"course_id": "C", "term_id": "T", "snapshot_day": [1] * 6 + [2] * 6, "student_id": range(12)})
    for c in FEATURES:
        df[c] = np.nan
    sc = tiers_per_snapshot(df, [0.9] * 12, {"high": {"threshold": 0.5}, "medium": None, "watch": None}, 0.5)
    assert sc.groupby("snapshot_day")["signal"].sum().tolist() == [3, 3]    # cap = 50% inside each day


def test_lead_time():
    sc = pd.DataFrame({"student_id": ["a"] * 3 + ["b"] * 2, "course_id": "C", "term_id": "T", "snapshot_day": [10, 20, 30, 10, 20],
                       "signal": [False, True, True, False, False], "outcome": ["Withdrawn"] * 5})
    wd = pd.DataFrame({"student_id": ["a", "b"], "course_id": "C", "term_id": "T", "day": [50, 60]})
    lt = lead_time(sc, wd)
    assert (lt["withdrawn_scorable"], lt["withdrawn_signalled"], lt["median_days"]) == (2, 1, 30.0)


# ---- end to end on synthetic data ----------------------------------------------------
@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    from disha_ml.rolling import train
    from disha_ml.rolling.schema import save_tables
    d = tmp_path_factory.mktemp("rolling")
    tables = make_tables()
    save_tables(tables, d / "tables")
    cfg = RollingConfig(train_terms=("T1",), test_terms=("T2",), cv_folds=3)
    manifest = train.run(str(d / "tables"), str(d / "art"), cfg)
    return d, tables, manifest


def test_training_writes_artifacts_and_reports_everything(trained):
    d, _, m = trained
    assert {p.name for p in (d / "art").iterdir()} == {"model.joblib", "manifest.json", "report.md"}
    r = m["results"]
    assert r["test_auc"] > 0.7 and m["parameters"]["total"] == m["parameters"]["split_nodes"] + m["parameters"]["leaves"] + m["parameters"]["calibration_points"]
    assert [a["term_fraction"] for a in r["auc_by_term_fraction"]] == [0.1, 0.25, 0.5, 0.75]
    assert {"HIGH", "MEDIUM", "WATCH", "ON_TRACK"} <= set(r["tiers"]) and "gender" in r["fairness"]
    assert "Overfitting check" in (d / "art" / "report.md").read_text()


def test_score_snapshot_payload(trained):
    from disha_ml.rolling.score import load_bundle, score_snapshot
    d, tables, _ = trained
    p = score_snapshot(tables, 60, load_bundle(d / "art"))
    js = json.loads(p.to_json())                                              # plain JSON, no NaN
    assert set(js) == {"schema_version", "as_of_day", "model", "n_students", "students", "cohorts", "data_drift"}
    assert js["n_students"] == len(js["students"]) > 0
    s = js["students"][0]
    assert set(s) == {"student_id", "course_id", "term_id", "as_of_day", "last_assessment", "risk", "reasons", "on_track",
                      "drift_events", "next_check", "snapshot", "history"}
    assert s["risk"]["tier"] in ("HIGH", "MEDIUM", "WATCH", "ON_TRACK") and len(s["reasons"]) <= 3
    assert all(h["day"] <= 60 for h in s["history"]) and s["next_check"]["day"] == 80
    c = js["cohorts"][0]
    assert sum(v["n"] for v in c["tier_distribution"].values()) == c["n_active"]
    assert c["time_to_risk"][-1]["day"] == 60 and js["data_drift"]["features"]
    # Withdrawn before day 60 means no row for that enrolment.
    gone = set(tables["withdrawals"].query("day <= 60")["student_id"])
    assert not gone & {x["student_id"] for x in js["students"]}
