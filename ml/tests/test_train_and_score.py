import json

import pandas as pd
import pytest

from disha_ml.config import TrainConfig
from disha_ml.data import load_dataset
from disha_ml.score import load_bundle, main as score_main, score_frame
from disha_ml.train import run


@pytest.fixture(scope="module")
def trained(sample_csv, tmp_path_factory):
    out = tmp_path_factory.mktemp("artifacts")
    cfg = TrainConfig(cv_folds=3)
    cfg.tiers.min_alerts = 15
    results = run(str(sample_csv), str(out), ["cp0", "cp1", "cp2"], cfg)
    return out, results


def test_artifacts_written(trained):
    out, _ = trained
    for cp in ("cp0", "cp1", "cp2"):
        m = json.loads((out / cp / "manifest.json").read_text())
        assert len(m["model_sha256"]) == 64
        assert (out / cp / "report.md").exists()
        assert m["test_metrics"]["n"] == 300


def test_later_checkpoints_know_more(trained):
    _, results = trained
    auc = {r["checkpoint"]: r["test_metrics"]["roc_auc"] for r in results}
    assert auc["cp1"] > auc["cp0"]


def test_signals_respect_capacity(trained):
    _, results = trained
    for r in results:
        assert r["test_signal"]["signal_rate"] <= 0.15 + 1e-9


def test_tampered_model_refused(trained, tmp_path):
    out, _ = trained
    target = tmp_path / "cp1"
    target.mkdir()
    (target / "model.joblib").write_bytes((out / "cp1" / "model.joblib").read_bytes() + b"x")
    (target / "manifest.json").write_text((out / "cp1" / "manifest.json").read_text())
    with pytest.raises(RuntimeError, match="does not match"):
        load_bundle(target)


def test_score_output_has_tiers_and_reasons(trained, sample_csv, tmp_path):
    out, _ = trained
    bundle = load_bundle(out / "cp1")
    raw = load_dataset(sample_csv).head(200)
    scored = score_frame(bundle, raw)
    assert set(scored["tier"]) <= {"HIGH", "MEDIUM", "WATCH", "ON_TRACK"}
    assert scored["risk_probability"].between(0, 1).all()

    # A student with no semester-1 record is not scored by cp1.
    gap = raw.copy()
    gap.loc[gap.index[0], [f"s1_{k}" for k in ("credited", "enrolled", "evaluations", "approved", "grade", "without_eval")]] = float("nan")
    gap_scored = score_frame(bundle, gap)
    assert gap_scored.iloc[0]["tier"] == "NO_DATA" and not gap_scored.iloc[0]["signal"]
    assert pd.isna(gap_scored.iloc[0]["risk_probability"])
    assert (gap_scored.iloc[1:]["tier"] != "NO_DATA").all()
    flagged = scored[scored["signal"]]
    assert (flagged["rule_reasons"].str.len() + flagged["model_factors"].str.len() > 0).all()

    # CLI: input without Target, with a display-only name column passed through.
    inp = pd.read_csv(sample_csv, sep=";").drop(columns=["Target"]).head(50)
    inp.insert(0, "name", [f"Student {i}" for i in range(50)])
    path_in, path_out = tmp_path / "in.csv", tmp_path / "out.csv"
    inp.to_csv(path_in, index=False)
    score_main(["--model", str(out / "cp1"), "--input", str(path_in), "--output", str(path_out)])
    res = pd.read_csv(path_out)
    assert "name" in res.columns and len(res) == 50
