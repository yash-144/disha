"""Train, calibrate, pick cutoffs, evaluate and save one model per checkpoint.

Usage:
    python -m kagaz_ml.train --data path/to/data.csv --out artifacts
    python -m kagaz_ml.train --data data.csv --out artifacts --checkpoints cp1 cp2 --label dropout
    python -m kagaz_ml.train --data my_students.csv --mapping mapping.json --out artifacts

Steps per checkpoint:
  1. Stratified split: 80% train, 20% test (same split for every checkpoint).
  2. Out-of-fold calibrated probabilities on train (5-fold).
  3. Pick HIGH / MEDIUM / WATCH cutoffs from those probabilities.
  4. Fit the calibrated model on all of train.
  5. Score the untouched test split once: metrics, tiers, fairness, baselines.
  6. Release check, then save model + manifest + report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from .config import CHECKPOINTS, RULES, TrainConfig
from .data import AUDIT_COLUMNS, available_checkpoints, file_sha256, load_dataset, load_mapping
from .evaluate import calibration_table, fairness_report, score_metrics, signal_metrics
from .explain import reference_values
from .features import build_features, explanation_groups, feature_columns
from .labels import make_label
from .models import build_estimator, calibrated
from .rules import rule_count
from .signal import assign_tiers
from .thresholds import choose_tier_cutoffs

ARTIFACT_VERSION = "1"


def _release_check(cfg: TrainConfig, cutoffs: Dict, test_signal: Dict, test_metrics: Dict, baselines: Dict) -> Dict:
    reasons: List[str] = []
    if not cutoffs["high"]:
        reasons.append(
            f"No cutoff reaches {cfg.tiers.high_precision:.0%} precision with at least "
            f"{cfg.tiers.min_alerts} students on training data: HIGH tier disabled."
        )
    hp = test_signal["tiers"]["HIGH"]["observed_rate"]
    if cutoffs["high"] and hp is not None and hp < cfg.tiers.high_precision - cfg.precision_tolerance:
        reasons.append(
            f"HIGH tier precision on test is {hp:.2f}, below target "
            f"{cfg.tiers.high_precision:.2f} minus tolerance {cfg.precision_tolerance:.2f}."
        )
    rules_pr = baselines.get("rules_only", {}).get("pr_auc")
    if rules_pr is not None and test_metrics["pr_auc"] <= rules_pr:
        reasons.append(f"Model PR AUC {test_metrics['pr_auc']:.3f} does not beat rules-only {rules_pr:.3f}.")
    advisories: List[str] = []
    lr_pr = baselines.get("logreg", {}).get("pr_auc")
    if lr_pr is not None and lr_pr >= test_metrics["pr_auc"] - 0.005:
        advisories.append(
            f"Logistic regression PR AUC {lr_pr:.3f} is within 0.005 of, or above, this model "
            f"({test_metrics['pr_auc']:.3f}); the simpler model (--model logreg) may be preferable."
        )
    return {"approved": not reasons, "reasons": reasons, "advisories": advisories}


def train_checkpoint(df: pd.DataFrame, checkpoint: str, cfg: TrainConfig, train_idx, test_idx) -> Dict:
    t0 = time.time()
    y = make_label(df, cfg.label).to_numpy()
    X = build_features(df, checkpoint)
    cols = feature_columns(checkpoint)
    # Drop features the dataset does not have at all (for example no admission grade).
    absent = [c for c in cols["numeric"] if X.loc[train_idx, c].isna().all()]
    if absent:
        print(f"[{checkpoint}] not in this dataset, left out of the model: {absent}")
    cols = {"numeric": [c for c in cols["numeric"] if c not in absent], "categorical": cols["categorical"]}
    X = X[cols["numeric"] + cols["categorical"]]
    # df has a 0..n-1 index (see run), so positions and labels agree.
    X_tr, X_te = X.loc[train_idx], X.loc[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    raw_te = df.loc[test_idx]

    def make(model_name: str):
        return calibrated(
            build_estimator(model_name, cols["numeric"], cols["categorical"], cfg.seed),
            cfg.calibration, cfg.cv_folds, cfg.seed,
        )

    # 2. Out-of-fold probabilities on train only.
    outer = StratifiedKFold(n_splits=cfg.cv_folds, shuffle=True, random_state=cfg.seed + 1)
    oof = cross_val_predict(make(cfg.model), X_tr, y_tr, cv=outer, method="predict_proba")[:, 1]

    # 3. Cutoffs from out-of-fold probabilities.
    cutoffs = choose_tier_cutoffs(y_tr, oof, cfg.tiers)

    # 4. Final model on all of train.
    model = make(cfg.model).fit(X_tr, y_tr)

    # 5. One look at the test split.
    p_te = model.predict_proba(X_te)[:, 1]
    rules_te = rule_count(raw_te, checkpoint).to_numpy()
    test_metrics = score_metrics(y_te, p_te)
    test_signal = signal_metrics(y_te, p_te, rules_te, cutoffs, cfg.tiers.capacity_share)

    _, sig_te, _ = assign_tiers(p_te, rules_te, cutoffs, cfg.tiers.capacity_share)
    audit = raw_te[[c for c in AUDIT_COLUMNS if c in raw_te.columns]]
    fairness = fairness_report(y_te, sig_te, audit) if not audit.empty else {}

    baselines: Dict[str, Dict] = {}
    if checkpoint != "cp0":
        baselines["rules_only"] = score_metrics(y_te, rules_te)
    if cfg.model != "logreg":
        lr = make("logreg").fit(X_tr, y_tr)
        baselines["logreg"] = score_metrics(y_te, lr.predict_proba(X_te)[:, 1])

    release = _release_check(cfg, cutoffs, test_signal, test_metrics, baselines)
    return {
        "checkpoint": checkpoint,
        "model": model,
        "features": cols,
        "reference": reference_values(X_tr, cols["categorical"]),
        "groups": explanation_groups(checkpoint),
        "cutoffs": cutoffs,
        "oof_metrics": score_metrics(y_tr, oof),
        "test_metrics": test_metrics,
        "test_signal": test_signal,
        "calibration_test": calibration_table(y_te, p_te),
        "baselines_test": baselines,
        "fairness_test": fairness,
        "release": release,
        "seconds": round(time.time() - t0, 1),
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(result: Dict, cfg: TrainConfig, out_dir: Path, data_sha: str, n_rows: int, mapping=None) -> Path:
    cp_dir = out_dir / result["checkpoint"]
    cp_dir.mkdir(parents=True, exist_ok=True)
    bundle = {
        "artifact_version": ARTIFACT_VERSION,
        "checkpoint": result["checkpoint"],
        "label": cfg.label,
        "model": result["model"],
        "features": result["features"],
        "reference": result["reference"],
        "groups": result["groups"],
        "cutoffs": result["cutoffs"],
        "capacity_share": cfg.tiers.capacity_share,
        "rules": RULES,
        "approved": result["release"]["approved"],
        "mapping": mapping,
    }
    model_path = cp_dir / "model.joblib"
    joblib.dump(bundle, model_path)
    manifest = {
        "artifact_version": ARTIFACT_VERSION,
        "checkpoint": result["checkpoint"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_sha256": _sha256_file(model_path),
        "data_sha256": data_sha,
        "rows": n_rows,
        "mapping": mapping,
        "config": cfg.to_dict(),
        "rules": RULES,
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__},
        "features": result["features"],
        "cutoffs": result["cutoffs"],
        "oof_metrics": result["oof_metrics"],
        "test_metrics": result["test_metrics"],
        "test_signal": result["test_signal"],
        "calibration_test": result["calibration_test"],
        "baselines_test": result["baselines_test"],
        "fairness_test": result["fairness_test"],
        "release": result["release"],
        "train_seconds": result["seconds"],
    }
    (cp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    (cp_dir / "report.md").write_text(render_report(manifest))
    return cp_dir


def _pct(x) -> str:
    return "n/a" if x is None else f"{x:.1%}"


def _num(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def render_report(m: Dict) -> str:
    t, s = m["test_metrics"], m["test_signal"]
    lines = [
        f"# Checkpoint {m['checkpoint']} · label `{m['config']['label']}` · model `{m['config']['model']}`",
        "",
        f"Release check: **{'APPROVED' if m['release']['approved'] else 'NOT APPROVED'}**",
    ]
    lines += [f"- {r}" for r in m["release"]["reasons"]]
    lines += [f"- Note: {a}" for a in m["release"].get("advisories", [])]
    lines += [
        "",
        "## Test split (never used for training or cutoffs)",
        "",
        f"| Students | At-risk rate | ROC AUC | PR AUC | Brier |",
        f"|---|---|---|---|---|",
        f"| {t['n']} | {_pct(t['base_rate'])} | {_num(t['roc_auc'])} | {_num(t['pr_auc'])} | {_num(t['brier'])} |",
        "",
        "## Cutoffs (chosen on out-of-fold training predictions)",
        "",
        "| Tier | Cutoff | Train precision | Train recall | Train flag rate |",
        "|---|---|---|---|---|",
    ]
    for tier, c in m["cutoffs"].items():
        if c:
            lines.append(f"| {tier} | {c['threshold']:.3f} | {_pct(c['precision'])} | {_pct(c['recall'])} | {_pct(c['flag_rate'])} |")
        else:
            lines.append(f"| {tier} | disabled | | | |")
    lines += [
        "",
        "## Signals on test",
        "",
        f"Signals raised: {s['signals']} ({_pct(s['signal_rate'])} of students) · "
        f"precision {_pct(s['signal_precision'])} · recall {_pct(s['signal_recall'])} · "
        f"removed by capacity cap: {s['capped']}",
        "",
        "| Tier | Students | Share | Actually at risk |",
        "|---|---|---|---|",
    ]
    for tier, v in s["tiers"].items():
        lines.append(f"| {tier} | {v['n']} | {_pct(v['share'])} | {_pct(v['observed_rate'])} |")
    if m["baselines_test"]:
        lines += ["", "## Baselines on test", "", "| Model | ROC AUC | PR AUC |", "|---|---|---|",
                  f"| this model | {_num(t['roc_auc'])} | {_num(t['pr_auc'])} |"]
        for name, b in m["baselines_test"].items():
            lines.append(f"| {name} | {_num(b['roc_auc'])} | {_num(b['pr_auc'])} |")
    if m["fairness_test"]:
        lines += ["", "## Fairness on test (audit columns are not model inputs)", ""]
        for col, rep in m["fairness_test"].items():
            lines.append(f"**{col}** · false-positive-rate ratio (max/min): {_num(rep['fpr_ratio_max_min'])}")
            lines += ["", "| Group | n | Signal rate | False-positive rate | Miss rate |", "|---|---|---|---|---|"]
            for g in rep["groups"]:
                lines.append(f"| {g['group']} | {g['n']} | {_pct(g['signal_rate'])} | "
                             f"{_pct(g['false_positive_rate'])} | {_pct(g['miss_rate'])} |")
            lines.append("")
    lines += ["", "## Calibration on test", "", "| Bin | n | Predicted | Observed |", "|---|---|---|---|"]
    for r in m["calibration_test"]:
        lines.append(f"| {r['bin']} | {r['n']} | {r['predicted']} | {r['observed']} |")
    return "\n".join(lines) + "\n"


def run(data: str, out: str, checkpoints: List[str], cfg: TrainConfig, mapping: Dict | None = None) -> List[Dict]:
    df = load_dataset(data, mapping=mapping).reset_index(drop=True)
    y = make_label(df, cfg.label)
    print(f"Rows: {len(df)}  outcomes: {df['target'].value_counts().to_dict()}  "
          f"label '{cfg.label}' positive rate: {y.mean():.1%}")
    supported = available_checkpoints(df)
    skipped = [cp for cp in checkpoints if cp not in supported]
    if skipped:
        print(f"Skipping {skipped}: the data lacks that semester's results for most students.")
    checkpoints = [cp for cp in checkpoints if cp in supported]
    train_idx, test_idx = train_test_split(
        df.index.to_numpy(), test_size=cfg.test_size, stratify=y, random_state=cfg.seed
    )
    out_dir = Path(out)
    data_sha = file_sha256(data)
    results = []
    for cp in checkpoints:
        r = train_checkpoint(df, cp, cfg, np.sort(train_idx), np.sort(test_idx))
        path = save(r, cfg, out_dir, data_sha, len(df), mapping)
        results.append(r)
        s, t = r["test_signal"], r["test_metrics"]
        print(
            f"[{cp}] {r['seconds']}s  ROC AUC {t['roc_auc']:.3f}  PR AUC {t['pr_auc']:.3f}  "
            f"signals {s['signals']} ({_pct(s['signal_rate'])})  precision {_pct(s['signal_precision'])}  "
            f"recall {_pct(s['signal_recall'])}  release={'APPROVED' if r['release']['approved'] else 'NOT APPROVED'}  -> {path}"
        )
        for reason in r["release"]["reasons"]:
            print(f"      - {reason}")
        for note in r["release"]["advisories"]:
            print(f"      note: {note}")
    return results


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Train risk-signal models per checkpoint.")
    ap.add_argument("--data", required=True)
    ap.add_argument("--mapping", default=None, help="mapping JSON for your own dataset (see kagaz_ml.mapping)")
    ap.add_argument("--out", default="artifacts")
    ap.add_argument("--checkpoints", nargs="+", default=CHECKPOINTS, choices=CHECKPOINTS)
    ap.add_argument("--label", default="dropout", choices=["dropout", "not_on_time"])
    ap.add_argument("--model", default="hgb", choices=["hgb", "logreg"])
    ap.add_argument("--calibration", default="isotonic", choices=["isotonic", "sigmoid"])
    ap.add_argument("--high-precision", type=float, default=None)
    ap.add_argument("--capacity-share", type=float, default=None)
    a = ap.parse_args(argv)
    cfg = TrainConfig(label=a.label, model=a.model, calibration=a.calibration)
    if a.high_precision is not None:
        cfg.tiers.high_precision = a.high_precision
    if a.capacity_share is not None:
        cfg.tiers.capacity_share = a.capacity_share
    run(a.data, a.out, a.checkpoints, cfg, load_mapping(a.mapping))


if __name__ == "__main__":
    main()
