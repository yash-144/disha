import numpy as np
import pandas as pd
import pytest

from disha_ml.data import AUDIT_COLUMNS, load_dataset, map_columns
from disha_ml.features import build_features, feature_columns
from disha_ml.labels import make_label
from disha_ml.synthetic import generate


def test_loads_semicolon_and_comma_and_header_variants(tmp_path):
    df = generate(50, seed=1)
    df = df.rename(columns={"Admission grade": " Admission  grade\t"})
    semi, comma = tmp_path / "a.csv", tmp_path / "b.csv"
    df.to_csv(semi, sep=";", index=False)
    df.to_csv(comma, sep=",", index=False)
    a, b = load_dataset(semi), load_dataset(comma)
    assert len(a) == len(b) == 50
    assert "admission_grade" in a.columns


def test_missing_required_column_is_an_error():
    df = generate(10).drop(columns=["Curricular units 1st sem (approved)"])
    with pytest.raises(ValueError, match="s1_approved"):
        map_columns(df)


def test_grade_zero_becomes_missing(sample_csv):
    df = load_dataset(sample_csv)
    no_pass = df["s1_approved"] == 0
    assert no_pass.any()
    assert df.loc[no_pass, "s1_grade"].isna().all()


@pytest.mark.parametrize("cp", ["cp0", "cp1"])
def test_no_future_semester_in_earlier_checkpoints(sample_csv, cp):
    X = build_features(load_dataset(sample_csv), cp)
    assert not [c for c in X.columns if c.startswith("s2_")]
    assert "grade_delta" not in X.columns
    if cp == "cp0":
        assert not [c for c in X.columns if c.startswith("s1_")]


@pytest.mark.parametrize("cp", ["cp0", "cp1", "cp2"])
def test_protected_columns_never_model_inputs(sample_csv, cp):
    X = build_features(load_dataset(sample_csv), cp)
    for c in AUDIT_COLUMNS + ["target"]:
        assert c not in X.columns
    cols = feature_columns(cp)
    assert set(cols["numeric"] + cols["categorical"]) == set(X.columns)


def test_rates_are_missing_when_no_units_enrolled():
    # Registered for nothing but has a credited subject: a real record, not a gap.
    raw = generate(20, seed=2)
    for k in ("enrolled", "approved", "evaluations", "without evaluations", "grade"):
        raw.loc[0, f"Curricular units 1st sem ({k})"] = 0
    raw.loc[0, "Curricular units 1st sem (credited)"] = 1
    df = load_dataset_from(raw)
    X = build_features(df, "cp1")
    assert np.isnan(X.loc[0, "s1_pass_rate"])
    assert X.loc[0, "s1_no_units"] == 1


def test_all_zero_semester_is_no_record_and_not_eligible():
    from disha_ml.data import eligible_rows
    raw = generate(20, seed=4)
    for s in ("1st", "2nd"):
        for k in ("credited", "enrolled", "approved", "evaluations", "without evaluations", "grade"):
            raw.loc[0, f"Curricular units {s} sem ({k})"] = 0
    df = load_dataset_from(raw)
    assert df.loc[0, ["s1_enrolled", "s1_approved", "s2_enrolled"]].isna().all()
    assert df.attrs["cleaning"]["s1_no_record_rows"] == 1
    assert eligible_rows(df, "cp0")[0] and not eligible_rows(df, "cp1")[0] and not eligible_rows(df, "cp2")[0]
    assert eligible_rows(df, "cp1")[1:].all()


def test_without_evaluation_capped_at_enrolled():
    raw = generate(20, seed=5)
    raw.loc[0, "Curricular units 2nd sem (enrolled)"] = 5
    raw.loc[0, "Curricular units 2nd sem (without evaluations)"] = 7
    df = load_dataset_from(raw)
    assert df.loc[0, "s2_without_eval"] == 5
    assert df.attrs["cleaning"]["s2_without_eval_capped_rows"] == 1


def test_labels():
    df = pd.DataFrame({"target": ["Dropout", "Enrolled", "Graduate"]})
    assert make_label(df, "dropout").tolist() == [1, 0, 0]
    assert make_label(df, "not_on_time").tolist() == [1, 1, 0]


def load_dataset_from(raw):
    from disha_ml.data import clean
    return clean(map_columns(raw))
