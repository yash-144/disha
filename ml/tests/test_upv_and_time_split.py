"""UPV converter, time-based split, the Retained outcome and the attendance input."""
import numpy as np
import pandas as pd
import pytest

from disha_ml.config import TrainConfig
from disha_ml.converters.upv import convert_frame
from disha_ml.data import clean, map_columns
from disha_ml.features import build_features, feature_columns
from disha_ml.labels import make_label
from disha_ml.synthetic import generate
from disha_ml.train import run, split_indices


def _upv_rows():
    """Two first-year students (several course rows each) and one second-year student."""
    base = {
        "tit_hash": "deg1", "caca": 2021, "curso_mas_bajo": 1, "nota10_hash": 7.5, "nota14_hash": 10.2,
        "desplazado_hash": "A", "cred_mat_sem_a": 30.0, "cred_sup_sem_a": 24.0, "cred_mat_sem_b": 24.0,
        "cred_sup_sem_b": 12.0, "cred_mat_anu": 6.0, "cred_sup_anu": 0.0,
        "n_wifi_days_2021_9": 10, "n_wifi_days_2021_10": 12, "n_wifi_days_2021_11": 14, "n_wifi_days_2021_12": 8,
        "n_wifi_days_2022_1": 6, "n_wifi_days_2022_2": 4, "n_wifi_days_2022_3": 2, "n_wifi_days_2022_4": 0,
        "n_wifi_days_2022_5": 0, "n_wifi_days_2022_6": 4,
    }
    rows = []
    for g in (6.0, 8.0):
        rows.append({**base, "dni_hash": "s1", "anyo_ingreso": 2021, "abandono_hash": "A", "nota_asig_hash": g})
    rows.append({**base, "dni_hash": "s2", "anyo_ingreso": 2021, "abandono_hash": "B", "nota_asig_hash": 5.0,
                 "n_wifi_days_2021_9": np.nan, "n_wifi_days_2021_10": np.nan})
    rows.append({**base, "dni_hash": "s3", "anyo_ingreso": 2019, "curso_mas_bajo": 2, "abandono_hash": "B",
                 "nota_asig_hash": 9.0})
    return pd.DataFrame(rows)


def test_upv_converter_maps_and_filters():
    out = convert_frame(_upv_rows()).set_index("student_id")
    assert list(out.index) == ["s1", "s2"]                       # s3 is not a first-year student
    s1 = out.loc["s1"]
    assert s1["s1_enrolled"] == 5.0 and s1["s1_approved"] == 4.0  # credits / 6
    assert s1["s2_enrolled"] == 5.0 and s1["s2_approved"] == 2.0  # sem B + year-long subjects
    assert s1["s2_grade"] == 14.0                                  # mean(6, 8) on 0-10 -> 0-20
    assert pd.isna(s1["s1_grade"])                                 # no semester-1 grade in UPV
    assert s1["s1_attendance"] == 10.0                             # mean Sep-Jan Wi-Fi days
    assert s1["s2_attendance"] == 2.0                              # mean Feb-Jun
    assert out.loc["s2", "s1_attendance"] == pytest.approx((14 + 8 + 6) / 3, abs=0.01)
    assert s1["target"] == "Dropout" and out.loc["s2", "target"] == "Retained"
    assert s1["cohort_year"] == 2021
    # The converted file loads with no mapping, and leakage columns are absent.
    df = clean(map_columns(out.reset_index()))
    assert "matricula_activa" not in df.columns and "baja_fecha" not in df.columns
    assert set(df["target"]) == {"Dropout", "Retained"}


def test_retained_blocks_not_on_time_label():
    df = pd.DataFrame({"target": ["Dropout", "Retained"]})
    assert make_label(df, "dropout").tolist() == [1, 0]
    with pytest.raises(ValueError, match="Retained"):
        make_label(df, "not_on_time")


def test_attendance_is_a_feature_but_never_from_a_later_semester():
    cols = feature_columns("cp1")["numeric"]
    assert "s1_attendance" in cols and "s2_attendance" not in cols
    assert "s2_attendance" in feature_columns("cp2")["numeric"]


def _with_cohorts(n=1500):
    df = generate(n, seed=7)
    df["cohort_year"] = np.where(np.arange(n) < n // 2, 2021, 2022)
    return df


def test_time_split_trains_on_earlier_and_tests_on_given_cohort():
    raw = clean(map_columns(_with_cohorts()))
    y = make_label(raw, "dropout")
    tr, te, note = split_indices(raw, y, TrainConfig(test_cohort="2022"))
    assert set(raw.loc[tr, "cohort_year"]) == {2021}
    assert set(raw.loc[te, "cohort_year"]) == {2022}
    assert "time-based" in note
    with pytest.raises(ValueError, match="before and"):
        split_indices(raw, y, TrainConfig(test_cohort="2021"))


def test_train_with_time_split_end_to_end(tmp_path):
    csv = tmp_path / "c.csv"
    _with_cohorts().to_csv(csv, sep=";", index=False)
    cfg = TrainConfig(cv_folds=3, test_cohort="2022")
    cfg.tiers.min_alerts = 15
    results = run(str(csv), str(tmp_path / "art"), ["cp1"], cfg)
    assert results[0]["test_metrics"]["n"] == 750
    assert "Time-based split" in (tmp_path / "art" / "cp1" / "report.md").read_text()


def test_attendance_flows_into_features_when_present():
    raw = generate(30, seed=8)
    raw["s1_attendance"] = 80.0
    X = build_features(clean(map_columns(raw)), "cp1")
    assert (X["s1_attendance"] == 80.0).all()
