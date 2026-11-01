# 17 · Model Training Guide

Step-by-step procedure to train, check and use the risk-signal models. Code is
in `ml/`. The method is explained in [16](16-risk-signal-pipeline.md).

> **Status (2026-11-01).** Sections 1 to 12 train the **legacy semester
> models** (`cp0`/`cp1`/`cp2`). The **primary rolling risk model** is trained
> and scored as in section 13.

## 1. Time and hardware

| Item | Value |
|---|---|
| Hardware | CPU only. A Kaggle CPU notebook or a laptop is enough; no GPU |
| Full run (3 checkpoints, calibration, cutoffs, baselines, reports) | About 15–20 seconds on a laptop for 4,424 rows (measured on synthetic data of that size) |
| Test suite | About 5–10 seconds |
| Realistic time budget | 1–2 hours to set up, run, read reports and try settings; the remaining time goes to the demo. The 6–10 hour ceiling is not needed for compute |

## 2. Setup

### On Kaggle
The dataset is committed at `ml/data/processed/data.csv`, so no Kaggle input
is needed.
1. New notebook; accelerator None (CPU); Internet on.
2. `!git clone https://github.com/yash-144/disha.git` then `%cd disha/ml`.
3. Kaggle images include scikit-learn, pandas, numpy and joblib.
4. Run: `!python kaggle_train.py`. It trains on the repository dataset by
   default; pass another CSV path (and `--mapping`) to use a different file.
5. Download `/kaggle/working/artifacts/` and `demo_scored_cp1.csv` from the
   Output panel.

### Locally
```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q
python -m disha_ml.train --data data/<dataset>.csv --out artifacts
```

**Version rule:** a saved model must be loaded with the same scikit-learn
version it was trained with. The version is recorded in each manifest.

### Own dataset
```bash
python -m disha_ml.mapping --data my_students.csv --out mapping.json   # template
# edit mapping.json: your headers, outcome values, grade_scale
python -m disha_ml.train --data my_students.csv --mapping mapping.json --out artifacts
```
Minimum columns: semester-1 subjects registered, semester-1 subjects passed,
final outcome. Checkpoints the data cannot support are skipped; absent
features are left out and logged. Full instructions: `ml/README.md` §17.

## 3. Step 1 — Load and clean

`disha_ml/data.py`:
- Detects `;` or `,` delimiter.
- Normalises headers (case, extra spaces, stray tabs) and maps them to short
  names; stops with a clear error if a required column is missing.
- Keeps only the 15 model source columns, 4 audit columns and the target.
- Turns semester grade 0 with no subjects passed into "missing".
- Stops if the target holds values other than Dropout / Graduate / Enrolled.
- Prints row count and outcome counts at the start of every run. Compare them
  with the dataset description before trusting anything else.

## 4. Step 2 — Label

`disha_ml/labels.py`. Choose with `--label`:

| Label | Positive (1) | Negative (0) | When to use |
|---|---|---|---|
| `dropout` (default) | Dropout | Graduate, Enrolled | Main demo: most serious outcome |
| `not_on_time` | Dropout, Enrolled | Graduate | Wider net: also catches students falling behind |

## 5. Step 3 — Features per checkpoint

`disha_ml/features.py` — see [16](16-risk-signal-pipeline.md) §5 for the list.
Tests enforce that `cp0` has no semester data, `cp1` has no semester-2 data,
and no checkpoint uses gender, age, displaced, special needs or the target.

## 6. Step 4 — Train, calibrate, choose cutoffs

`disha_ml/train.py`, per checkpoint:

1. **Split** once: 80% train, 20% test, stratified by label, seed 42. The same
   students are in the test set for every checkpoint.
2. **Out-of-fold scores:** 5-fold cross-validation on train; each fold's model
   is calibrated (isotonic) inside its own training part.
3. **Cutoffs** from the out-of-fold scores (method in
   [16](16-risk-signal-pipeline.md) §7). Defaults in `disha_ml/config.py`:

   | Setting | Default | Meaning |
   |---|---|---|
   | `high_precision` | 0.85 | HIGH tier target precision |
   | `medium_precision` | 0.70 | MEDIUM tier target (needs a rule as well) |
   | `watch_precision` | 0.50 | WATCH list target |
   | `min_alerts` | 30 | Minimum students above a cutoff for it to count |
   | `capacity_share` | 0.15 | Maximum share of a cohort that gets a signal |
   | `precision_tolerance` | 0.05 | Allowed shortfall on test before the release check fails |

4. **Final model** fitted on all of train. It is **not** refitted on the test
   rows, so the test results describe exactly the saved model.
5. **Baselines** on the same test split: rules-only score (number of rules
   fired) and logistic regression.

## 7. Step 5 — Read the report

Each checkpoint writes `artifacts/<cp>/report.md` and `manifest.json`.
Check in this order:

| Section | Look for |
|---|---|
| Release check | `APPROVED`, or the reasons it was not |
| Test split | ROC AUC and PR AUC; PR AUC is the more useful one when positives are a minority |
| Cutoffs | Which tiers are enabled; recall at HIGH |
| Signals on test | Signal precision near or above target; signal rate ≤ capacity; how many were capped |
| Tiers table | "Actually at risk" should fall from HIGH → MEDIUM → WATCH → ON_TRACK |
| Baselines | Model PR AUC > rules-only. If logistic regression is equal or better, a note recommends `--model logreg` |
| Fairness | Signal rate and false-positive rate per group; the max/min false-positive ratio |
| Calibration | Predicted ≈ observed in each bin |

## 8. Step 6 — Release check

A checkpoint model is **approved** only if all hold:
- A HIGH cutoff exists on training data at the target precision.
- HIGH-tier precision on test ≥ target − tolerance.
- Model PR AUC on test > rules-only PR AUC (`cp1`, `cp2`).

Not approved → the scorer still runs but marks every row "model not approved
by release check; show for review only".

**Open decision:** an acceptable bound for the fairness false-positive ratio
(the code reports it; it does not yet block release).

## 9. Tuning order if results are weak

Change one thing at a time and re-run:

1. `--model logreg` vs `hgb`.
2. `--calibration sigmoid` if a checkpoint has few positives.
3. `--label not_on_time` if dropout alone gives too few positives for a HIGH
   cutoff.
4. Lower `--high-precision` (for example 0.80) only with a stated reason; never
   lower it just to make the demo show more alerts.
5. Rule thresholds in `config.py` (`RULES`) affect MEDIUM corroboration and
   reason texts.

Do not tune on the test split. Every change is judged by the out-of-fold
numbers; the test split is read once at the end.

## 10. Step 7 — Score students (demo)

```bash
python -m disha_ml.score --model artifacts/cp1 --input students.csv --output scored.csv
```

- Input: same headers as training; `Target` not needed. Columns `student_id`,
  `roll_no`, `name` are copied to the output for display, never used by the
  model.
- The scorer verifies the model file's SHA-256 against the manifest and refuses
  to load on mismatch.
- Output columns: `risk_probability`, `tier`, `signal`, `capacity_capped`,
  `rule_reasons`, `rule_codes`, `model_factors`, and `note` if not approved.
- The capacity cap applies to the file being scored, so score one cohort per
  file.
- `kaggle_train.py` also writes `demo_scored_cp1.csv` over all rows with the
  real outcome attached. It includes training rows, so it is for display only;
  accuracy figures come from `report.md`.

For the demo UI, display names can be added to the scored file. If names are
invented for display, label them as sample names.

## 11. Moving to real campus data

1. Map campus exports to the same canonical columns
   ([18](18-dataset-requirements.md) §4); add attendance and internal marks.
2. Build at least one full past year of students with known outcomes.
3. Replace the random split with a **time split**: train on older cohorts,
   test on the newest. The UCI dataset has no year column, which is why it uses
   a random stratified split.
4. Re-run; compare against the UCI-trained model on the campus test cohort.
   Use the campus-trained model only if it passes the release check there.
5. After deployment, each recorded case outcome
   ([07](07-case-workflow-and-worker.md)) becomes a label for the next
   retraining. Retrain once per term; monitor alert rate and precision as in
   [08](08-ml-subsystem.md) §7.

## 12. Files

| File | Role |
|---|---|
| `ml/disha_ml/config.py` | All settings, cutoff targets, rule thresholds |
| `ml/disha_ml/data.py` | Load, map columns (UCI or mapping file), rescale grades, map outcomes, clean |
| `ml/disha_ml/mapping.py` | Mapping-template generator for your own dataset |
| `ml/disha_ml/labels.py` | Label definitions |
| `ml/disha_ml/features.py` | Checkpoint features, explanation groups |
| `ml/disha_ml/rules.py` | Academic rules and reason texts |
| `ml/disha_ml/models.py` | Model pipelines and calibration |
| `ml/disha_ml/thresholds.py` | Precision-based cutoff selection |
| `ml/disha_ml/signal.py` | Tier logic and capacity cap |
| `ml/disha_ml/explain.py` | Per-student factor contributions |
| `ml/disha_ml/evaluate.py` | Metrics, calibration table, fairness |
| `ml/disha_ml/train.py` | Training CLI, release check, report |
| `ml/disha_ml/score.py` | Scoring CLI with model hash check |
| `ml/disha_ml/synthetic.py` | Invented data for tests only |
| `ml/kaggle_train.py` | One-command Kaggle runner |
| `ml/tests/` | Leakage, protected-column, cutoff, tier, end-to-end tests |

## 13. The rolling risk model (primary)

Code: `ml/disha_ml/rolling/`. Background: [16](16-risk-signal-pipeline.md) §12.

### 13.1 Data

OULAD (CC BY 4.0) in `ml/data/raw/oulad/` (git-ignored; the tracked note
`SOURCE.md` has the Internet Archive URL, size and SHA-256). Recreate it by
downloading the zip named there and running `unzip -j` into that folder. Convert
to the canonical tables:

```bash
cd ml
python -m disha_ml.converters.oulad --raw data/raw/oulad --out data/processed/oulad
```

### 13.2 Train

```bash
python -m disha_ml.rolling.train --data data/raw/oulad --out artifacts_rolling --no-meko
```

`--data` accepts raw OULAD CSVs (converted and cached) or a folder of canonical
tables. About 107 s on CPU. Settings (`RollingConfig` in `rolling/config.py`):
train terms 2013B / 2013J / 2014B, test term 2014J, fixed term fractions 0.1 /
0.25 / 0.5 / 0.75, isotonic calibration, 5 folds grouped by student, seed 42,
precision targets 0.85 / 0.70 / 0.50, minimum 30 alerts, capacity share 0.25.

Output in `ml/artifacts_rolling/`: `model.joblib`, `manifest.json` (config,
rules, features, all metrics, parameter count, `studentInfo.csv` SHA-256),
`report.md`. Read `report.md` in this order: test metrics, AUC by term fraction,
lead time, tiers, overfitting check (train vs CV vs test), model size, fairness
slices.

### 13.3 Score

```bash
python -m disha_ml.rolling.score --tables data/processed/oulad --as-of 120 --out insights.json --no-meko
```

Library: `score_snapshot(tables, as_of) -> InsightsPayload`. Payload and field
definitions: [`docs/architecture/INSIGHTS_SPEC.md`](../docs/architecture/INSIGHTS_SPEC.md).
Scoring all 32k OULAD enrolments takes about 15 s, so score per course-term or
per day. Without `--no-meko`, tier-change memories are written to Meko
([`docs/architecture/MEKO_INTEGRATION.md`](../docs/architecture/MEKO_INTEGRATION.md)).

### 13.4 Tests

`ml/tests/test_rolling.py` (no data after day t, withdrawn rows excluded,
student-grouped folds, hand-built features, schema validation, reasons, drift,
PSI, ECE, per-snapshot cap, lead time, end-to-end train and score) and
`ml/tests/test_meko_hooks.py`.

### 13.5 Retraining and moving to campus data

Replace OULAD with the campus tables ([18](18-dataset-requirements.md) §7 and
§9), keep the temporal split (train on earlier terms, test on the newest), and
compare against the OULAD model on the campus test term. **Not yet
implemented:** a release check and fairness bound for the rolling trainer
(the legacy trainer has one), and automatic retraining from case outcomes.

