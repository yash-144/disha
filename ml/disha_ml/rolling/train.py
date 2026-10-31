"""Train the rolling risk model.

    python -m disha_ml.rolling.train --data ml/data/raw/oulad

--data is either a folder of raw OULAD CSVs (converted on the fly and cached under
data/processed/oulad) or a folder of canonical tables (disha_ml.rolling.schema).
Writes model.joblib, manifest.json and report.md to ml/artifacts_rolling/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from .. import meko_hooks
from ..explain import reference_values
from ..models import build_estimator, calibrated
from ..thresholds import choose_tier_cutoffs
from . import evaluate as ev
from .config import DRIFT, MIN_EFFECT, RULES, RollingConfig
from .features import FEATURES, GROUPS, build_snapshots
from .schema import AUDIT_COLUMNS, load_tables, validate

BUNDLE_VERSION = 1


def group_splits(groups, folds: int, seed: int) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Shuffled GroupKFold: no student (group) is on both sides of any split."""
    return list(GroupKFold(n_splits=folds, shuffle=True, random_state=seed).split(np.zeros(len(groups)), groups=groups))


def fit_model(X: pd.DataFrame, y, groups, cfg: RollingConfig):
    """HGB + isotonic calibration, with calibration folds grouped by student."""
    splits = group_splits(np.asarray(groups), cfg.cv_folds, cfg.seed)
    est = build_estimator("hgb", FEATURES, [], cfg.seed)
    return calibrated(est, cfg.calibration, cfg.cv_folds, cfg.seed, cv=splits).fit(X, y)


def out_of_fold(X: pd.DataFrame, y, groups, cfg: RollingConfig) -> np.ndarray:
    """Out-of-fold probabilities on train; each fold's calibration is itself grouped by student."""
    y, groups = np.asarray(y), np.asarray(groups)
    oof = np.zeros(len(y))
    for tr, te in group_splits(groups, cfg.cv_folds, cfg.seed + 1):
        m = fit_model(X.iloc[tr], y[tr], groups[tr], RollingConfig(**{**cfg.__dict__, "cv_folds": 3}))
        oof[te] = m.predict_proba(X.iloc[te])[:, 1]
    return oof


def load_data(path: str) -> Dict[str, pd.DataFrame]:
    p = Path(path)
    if (p / "studentInfo.csv").exists():  # raw OULAD
        from ..converters.oulad import convert
        from .schema import save_tables
        cache = Path("data/processed/oulad")
        if (cache / "enrolments.csv.gz").exists() and (cache / "enrolments.csv.gz").stat().st_mtime > (p / "studentInfo.csv").stat().st_mtime:
            return load_tables(cache)
        tables = convert(p)
        save_tables(tables, cache)
        return tables
    return load_tables(p)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(data: str, out: str, cfg: RollingConfig) -> Dict:
    t0 = time.time()
    tables = load_data(data)
    snaps = build_snapshots(tables, cfg.fixed_fracs)
    tr_m, te_m = snaps["term_id"].isin(cfg.train_terms), snaps["term_id"].isin(cfg.test_terms)
    tr, te = snaps[tr_m].reset_index(drop=True), snaps[te_m].reset_index(drop=True)
    print(f"snapshots: train {len(tr)} rows / {tr.student_id.nunique()} students, test {len(te)} rows / {te.student_id.nunique()} students")
    X_tr, X_te, y_tr, y_te = tr[FEATURES], te[FEATURES], tr["at_risk"].to_numpy(), te["at_risk"].to_numpy()

    oof = out_of_fold(X_tr, y_tr, tr["student_id"], cfg)
    cutoffs = choose_tier_cutoffs(y_tr, oof, cfg.tiers)
    model = fit_model(X_tr, y_tr, tr["student_id"], cfg)
    p_tr, p_te = model.predict_proba(X_tr)[:, 1], model.predict_proba(X_te)[:, 1]

    sc = ev.tiers_per_snapshot(te, p_te, cutoffs, cfg.tiers.capacity_share)
    auc_tr, auc_cv, auc_te = (roc_auc_score(y_tr, p_tr), roc_auc_score(y_tr, oof), roc_auc_score(y_te, p_te))
    seen = te["student_id"].isin(set(tr["student_id"])).to_numpy()
    new_auc = roc_auc_score(y_te[~seen], p_te[~seen]) if (~seen).any() else None
    students = tables["students"]
    results = {
        "test": ev.headline(y_te, p_te), "train_auc": auc_tr, "cv_auc": auc_cv, "test_auc": auc_te,
        "gap_train_cv": auc_tr - auc_cv, "gap_cv_test": auc_cv - auc_te,
        "test_auc_unseen_students": new_auc, "test_students_seen_in_train": float(seen.mean()),
        "rules_only_auc": float(roc_auc_score(y_te, sc["rule_n"])),
        "auc_by_term_fraction": ev.auc_by_term_fraction(te, p_te, cfg.fixed_fracs),
        "tiers": ev.tier_table(sc), "lead_time": ev.lead_time(sc, tables["withdrawals"]),
        "fairness": ev.fairness(sc, students), "calibration_oof": ev.ece(y_tr, oof),
    }
    params = ev.parameter_count(model)
    ref = reference_values(X_tr, [])
    # PSI reference: the training cohorts at each fixed term fraction (one row per enrolment per fraction).
    fixed = tr["frac_tag"].notna()
    sample = pd.concat([X_tr[fixed].astype("float32"), tr.loc[fixed, ["frac_tag"]]], axis=1)
    seconds = round(time.time() - t0, 1)

    outp = Path(out)
    outp.mkdir(parents=True, exist_ok=True)
    bundle = {"version": BUNDLE_VERSION, "model": model, "features": FEATURES, "groups": GROUPS, "reference": ref,
              "cutoffs": cutoffs, "capacity_share": cfg.tiers.capacity_share, "psi_reference": sample,
              "fixed_fracs": cfg.fixed_fracs, "trained_terms": cfg.train_terms}
    joblib.dump(bundle, outp / "model.joblib", compress=3)
    size = (outp / "model.joblib").stat().st_size
    raw_info = Path(data) / "studentInfo.csv"
    manifest = {
        "model": "rolling-hgb-isotonic", "bundle_version": BUNDLE_VERSION, "dataset": "OULAD (CC BY 4.0), see data/raw/oulad/SOURCE.md",
        "studentInfo_sha256": _sha(raw_info) if raw_info.exists() else None,
        "config": cfg.to_dict(), "rules": RULES, "drift_events": DRIFT, "min_effect": MIN_EFFECT,
        "features": FEATURES, "feature_groups": GROUPS, "excluded_as_inputs": AUDIT_COLUMNS,
        "rows": {"train": len(tr), "test": len(te), "train_students": int(tr.student_id.nunique()),
                 "test_students": int(te.student_id.nunique()), "train_base_rate": float(y_tr.mean()),
                 "test_base_rate": float(y_te.mean())},
        "cutoffs": cutoffs, "parameters": params, "artifact_bytes": size, "train_seconds": seconds,
        "results": results,
        "libs": {"python": platform.python_version(), "sklearn": sklearn.__version__, "pandas": pd.__version__, "numpy": np.__version__},
    }
    (outp / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float))
    (outp / "report.md").write_text(render_report(manifest))
    print(f"test AUC {auc_te:.3f} (train {auc_tr:.3f}, CV {auc_cv:.3f}); {params['total']} parameters; "
          f"{size / 1e6:.1f} MB; {seconds}s -> {outp}")
    return manifest


def _p(x, d=1):
    return "n/a" if x is None else f"{100 * x:.{d}f}%"


def render_report(m: Dict) -> str:
    r, t = m["results"], m["results"]["test"]
    L = ["# Rolling risk model report", "",
         f"Dataset: {m['dataset']}. Train terms {m['config']['train_terms']}, test terms {m['config']['test_terms']}.",
         f"Rows: train {m['rows']['train']:,} ({m['rows']['train_students']:,} students, base rate {_p(m['rows']['train_base_rate'])}), "
         f"test {m['rows']['test']:,} ({m['rows']['test_students']:,} students, base rate {_p(m['rows']['test_base_rate'])}). "
         "One row = one student in one course-term at one snapshot day.", "",
         "## Test metrics (all snapshots of the held-out term)", "",
         "| ROC-AUC | PR-AUC | Brier | ECE | Accuracy | Majority baseline |", "|---|---|---|---|---|---|",
         f"| {t['roc_auc']:.3f} | {t['pr_auc']:.3f} | {t['brier']:.3f} | {t['ece']:.3f} | {_p(t['accuracy'])} | {_p(t['majority_accuracy'])} |",
         f"\nRules-only score AUC for comparison: {r['rules_only_auc']:.3f}.", "",
         "## How early can we catch them (AUC at a fraction of the term)", "",
         "| Term elapsed | Rows | Base rate | ROC-AUC |", "|---|---|---|---|"]
    L += [f"| {int(a['term_fraction'] * 100)}% | {a['n']:,} | {_p(a['base_rate'])} | "
          f"{'n/a' if a['roc_auc'] is None else format(a['roc_auc'], '.3f')} |" for a in r["auc_by_term_fraction"]]
    lt = r["lead_time"]
    L += ["", "## Lead time", "",
          f"Withdrawn students with at least one snapshot: {lt['withdrawn_scorable']:,}. Signalled (HIGH or MEDIUM) before withdrawing: "
          f"{lt['withdrawn_signalled']:,} ({_p(lt['detection_rate'])}). Days between first signal and withdrawal: median "
          f"{lt['median_days']}, interquartile {lt['p25_days']} to {lt['p75_days']}.", "",
          "## Tiers (test; capacity cap applied per course, term and day)", "",
          "Cutoffs on out-of-fold probability: " + ", ".join(
              f"{k.upper()} {v['threshold']:.3f} (precision target met at {_p(v['precision'])})" if v else f"{k.upper()} none"
              for k, v in m["cutoffs"].items()) + f". Capacity cap {_p(m['config']['tiers']['capacity_share'], 0)} of active students.", "",
          "| Tier | n | Share | Precision | Recall |", "|---|---|---|---|---|"]
    L += [f"| {k} | {v['n']:,} | {_p(v['share'])} | {_p(v['precision'])} | {_p(v['recall'])} |" for k, v in r["tiers"].items()]
    L += ["", "## Overfitting check", "",
          "| Train AUC | CV AUC (grouped by student) | Test AUC | Train-CV gap | CV-test gap |", "|---|---|---|---|---|",
          f"| {r['train_auc']:.3f} | {r['cv_auc']:.3f} | {r['test_auc']:.3f} | {r['gap_train_cv']:+.3f} | {r['gap_cv_test']:+.3f} |",
          f"\n{_p(r['test_students_seen_in_train'])} of test rows belong to students who also appear in a training term "
          f"(repeaters). Test AUC on unseen students only: "
          f"{'n/a' if r['test_auc_unseen_students'] is None else format(r['test_auc_unseen_students'], '.3f')}.", "",
          "## Model size", "", f"{m['parameters']['total']:,} parameters = {m['parameters']['split_nodes']:,} tree split nodes + "
          f"{m['parameters']['leaves']:,} leaves + {m['parameters']['calibration_points']:,} isotonic calibration points, over "
          f"{m['parameters']['trees']:,} trees in {m['parameters']['folds']} calibration folds (averaged at prediction time). Artifact {m['artifact_bytes'] / 1e6:.2f} MB; trained in {m['train_seconds']}s.", "",
          "## Fairness slices (signal rate and false-positive rate by group; demographics are NOT model inputs)", ""]
    for col, rep in r["fairness"].items():
        L += [f"**{col}** (FPR max/min ratio: {rep['fpr_ratio_max_min'] and round(rep['fpr_ratio_max_min'], 2)})", "",
              "| Group | n | Signal rate | FPR | Miss rate |", "|---|---|---|---|---|"]
        L += [f"| {g['group']} | {g['n']:,} | {_p(g['signal_rate'])} | {_p(g['false_positive_rate'])} | {_p(g['miss_rate'])} |"
              for g in rep["groups"]]
        L.append("")
    L += ["## Features", "", ", ".join(m["features"]), ""]
    return "\n".join(L)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Train the rolling risk model")
    ap.add_argument("--data", default="data/raw/oulad")
    ap.add_argument("--out", default="artifacts_rolling")
    ap.add_argument("--no-meko", action="store_true", help="never talk to Meko")
    a = ap.parse_args(argv)
    if a.no_meko:
        meko_hooks.disable()
    run(a.data, a.out, RollingConfig())


if __name__ == "__main__":
    main()
