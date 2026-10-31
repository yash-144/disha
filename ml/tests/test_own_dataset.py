"""Own dataset: different headers, SGPA on a 0-10 scale, different outcome
labels, and no semester-2 data."""
import json

import numpy as np
import pandas as pd
import pytest

from kagaz_ml.config import TrainConfig
from kagaz_ml.data import load_dataset, load_mapping
from kagaz_ml.mapping import build_template, main as mapping_main
from kagaz_ml.score import main as score_main
from kagaz_ml.synthetic import generate
from kagaz_ml.train import run

RENAME = {
    "Previous qualification (grade)": "Class 12 %",
    "Course": "Branch",
    "Curricular units 1st sem (enrolled)": "Sem1 Subjects Registered",
    "Curricular units 1st sem (approved)": "Sem1 Subjects Cleared",
    "Curricular units 1st sem (evaluations)": "Sem1 Exams Appeared",
    "Curricular units 1st sem (without evaluations)": "Sem1 Exams Absent",
    "Curricular units 1st sem (grade)": "Sem1 SGPA",
    "Gender": "Sex",
    "Target": "Status",
}
OUTCOMES = {"Dropout": "Dropped out", "Graduate": "Passed out", "Enrolled": "Continuing"}

MAPPING = {
    "columns": {
        "prev_qual_grade": "Class 12 %",
        "admission_grade": None,
        "course": "Branch",
        "s1_enrolled": "Sem1 Subjects Registered",
        "s1_approved": "Sem1 Subjects Cleared",
        "s1_evaluations": "Sem1 Exams Appeared",
        "s1_without_eval": "Sem1 Exams Absent",
        "s1_grade": "Sem1 SGPA",
        "s1_credited": None,
        "gender": "Sex",
        "target": "Status",
    },
    "target_values": {"Dropped out": "Dropout", "Passed out": "Graduate", "Continuing": "Enrolled"},
    "grade_scale": 10,
}


@pytest.fixture(scope="module")
def own_csv(tmp_path_factory):
    df = generate(1500, seed=3)
    df["Curricular units 1st sem (grade)"] = df["Curricular units 1st sem (grade)"] / 2  # 0-20 -> SGPA 0-10
    df["Target"] = df["Target"].map(OUTCOMES)
    keep = list(RENAME)
    df = df[keep].rename(columns=RENAME)
    df.insert(0, "name", [f"Sample Student {i}" for i in range(len(df))])
    path = tmp_path_factory.mktemp("own") / "college.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture(scope="module")
def mapping_file(own_csv):
    p = own_csv.parent / "mapping.json"
    p.write_text(json.dumps(MAPPING))
    return p


def test_without_mapping_gives_clear_error(own_csv):
    with pytest.raises(ValueError, match="mapping"):
        load_dataset(own_csv)


def test_template_guesses_outcomes_and_lists_headers(own_csv, tmp_path):
    tpl = build_template(str(own_csv))
    assert "Sem1 SGPA" in tpl["_headers_in_your_file"]
    out = tmp_path / "m.json"
    mapping_main(["--data", str(own_csv), "--out", str(out)])
    assert json.loads(out.read_text())["columns"]["s1_enrolled"] is None  # not auto-matched; user fills it
    guesses = {k: v for k, v in build_template(str(own_csv))["target_values"].items()}
    assert guesses == {}  # 'Status' header is not auto-detected, so no outcome guesses yet


def test_outcome_guessing():
    from kagaz_ml.mapping import _guess_outcome
    assert _guess_outcome("Dropped out") == "Dropout"
    assert _guess_outcome("Passed out") == "Graduate"
    assert _guess_outcome("Continuing") == "Enrolled"


def test_mapping_loads_and_rescales_grades(own_csv, mapping_file):
    df = load_dataset(own_csv, mapping=load_mapping(mapping_file))
    assert set(df["target"]) <= {"Dropout", "Graduate", "Enrolled"}
    assert df["s1_grade"].max() <= 20 and df["s1_grade"].max() > 10   # rescaled from 0-10
    assert df["admission_grade"].isna().all()
    assert "name" not in df.columns


def test_bad_mapping_rejected(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"columns": {"attendance": "Att %"}}))
    with pytest.raises(ValueError, match="unknown canonical"):
        load_mapping(p)
    p.write_text(json.dumps({"target_values": {"x": "Failed"}}))
    with pytest.raises(ValueError, match="target_values"):
        load_mapping(p)


def test_unmapped_outcome_value_rejected(own_csv, tmp_path):
    m = json.loads(json.dumps(MAPPING))
    del m["target_values"]["Continuing"]
    p = tmp_path / "m.json"
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError, match="Continuing"):
        load_dataset(own_csv, mapping=load_mapping(p))


def test_train_and_score_own_dataset(own_csv, mapping_file, tmp_path):
    cfg = TrainConfig(cv_folds=3)
    cfg.tiers.min_alerts = 15
    out = tmp_path / "artifacts"
    results = run(str(own_csv), str(out), ["cp0", "cp1", "cp2"], cfg, load_mapping(mapping_file))
    assert [r["checkpoint"] for r in results] == ["cp0", "cp1"]          # cp2 skipped: no semester 2
    assert not (out / "cp2").exists()
    manifest = json.loads((out / "cp1" / "manifest.json").read_text())
    assert manifest["mapping"]["grade_scale"] == 10

    inp = pd.read_csv(own_csv).drop(columns=["Status"]).head(40)
    path_in, path_out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.to_csv(path_in, index=False)
    score_main(["--model", str(out / "cp1"), "--input", str(path_in), "--output", str(path_out)])
    res = pd.read_csv(path_out)
    assert len(res) == 40 and "name" in res.columns
    assert np.isfinite(res["risk_probability"]).all()
