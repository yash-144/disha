# 08 · ML Subsystem

The ML subsystem is optional. The rules engine ([06](06-ingestion-and-rules-engine.md))
is the primary source of signals. A model adds a supplementary risk estimate
to a signal; it never opens a case (INV-01).

**First implementation:** the pipeline built on the public UCI dropout dataset
(academic columns only), with calibrated probabilities, precision-based tier
cutoffs, rule corroboration and a capacity cap, is specified in
[16-risk-signal-pipeline.md](16-risk-signal-pipeline.md), with the training
procedure in [17-model-training-guide.md](17-model-training-guide.md) and data
requirements in [18-dataset-requirements.md](18-dataset-requirements.md).
Code: `ml/kagaz_ml/`. Sections 2–8 below remain the requirements for moving
that pipeline to real campus data. Section 1 describes the earlier OULAD model
in the SUTRA repository, kept as reference.

## 1. Facts about the current model

Sources: `ml/artifacts/models/v1.0.0/model_metadata.json`,
`app/schemas/ml.py`, `app/ml/service.py`, audit section "ML pipeline".

| Item | Value |
|---|---|
| Training data | OULAD (Open University Learning Analytics Dataset), UK distance learning, 2013–14 |
| Label | Fail or Withdrawn, predicted at day 30 of a course presentation |
| Algorithm | `Pipeline(ColumnTransformer, LogisticRegression)` (regularised) |
| Inputs | 25 features (list below); 19 are OULAD-specific (VLE click counts by resource type, banked assessments) |
| Protected / proxy inputs | `gender`, `disability`, `age_band`, `imd_band`, `region` |
| Decision threshold | 0.46 |
| Test-set alert rate at threshold | 51% of students |
| Precision at threshold | 56% |
| ROC AUC (test) | 0.72 |
| CV baseline (threshold 0.5) | n = 18,263; prevalence 0.4564; precision 0.627; recall 0.650; ROC AUC 0.723; PR AUC 0.694; Brier 0.212 |
| Calibration | None in the served artifact; the API labels every prediction `platt_calibrated` (audit M4) |
| Artifact storage | `ml/artifacts/models/*` git-ignored; 9 experiment `.joblib` files committed (audit M5) |
| Model version | Hardcoded `1.0.0` in `MLService` (audit D6) |
| Research candidate | Constrained XGBoost `0.1.0-research`, not served |
| Research scope | 19 pipeline scripts, reports for 23 "phases" (audit M6) |
| Product use | `/students/{id}/predict` refuses real students because VLE features cannot be derived from institutional data (`app/api/v1/students.py:571`) (audit M1) |

Current feature list (`DAY30_REQUIRED_FEATURES`):
`num_of_prev_attempts, studied_credits, gender, region, highest_education,
imd_band, age_band, disability, days_registered_before_start,
has_missing_registration_date, vle_total_clicks_d30, vle_active_days_d30,
vle_clicks_precourse, vle_clicks_poststart_d30, vle_clicks_last_7d,
vle_days_since_last_click, vle_clicks_forumng_d30, vle_clicks_oucontent_d30,
vle_clicks_quiz_d30, vle_clicks_homepage_d30, vle_clicks_other_d30,
has_vle_activity_d30, assessments_submitted_d30, assessment_banked_d30,
has_early_assessment_submission_d30`.

Forbidden (leakage) features enforced today: `final_result, is_at_risk,
at_risk, date_unregistration, score, assessment_score, early_assessment_score,
student_id, id_student`.

Subgroup results at the operating threshold
(`ml/reports/metrics/phase_six_subgroup_metrics.csv`):

| Subgroup | Students | Alert rate | False-positive rate |
|---|---|---|---|
| IMD 0–10% (most deprived) | 820 | 79.6% | 0.69 |
| IMD 90–100% (least deprived) | 747 | 29.2% | 0.20 |
| Disability: yes | 854 | 72.3% | 0.58 |
| Disability: no | 8,349 | 49.0% | 0.37 |

Methods present in the current research code (audit: "What to keep"):
temporal split by course presentation, CV grouped by student, day-30 leakage
guard, checksum-verified dataset download, fixed seeds, subgroup metrics.

## 2. Preconditions for building a model

- **ML-PRE-01** A signed data-sharing agreement with at least one partner
  institution (audit roadmap).
- **ML-PRE-02** Historical data from that institution covering inputs and a
  defined outcome label for at least one full academic cycle.
- **ML-PRE-03** Legal review of the use of student data, including minors,
  under India's DPDP Act 2023.

Until these hold, the ML module ships disabled and the API returns
`ML_UNAVAILABLE` for prediction routes.

## 3. Feature contract

**Requirement ML-FC-01 (audit M1):** features are defined only from data the
partner institution actually holds and that the ingestion contract can carry.
The first implemented contract (prior grades, course, per-semester subject
counts, grades and derived rates) is listed in
[16](16-risk-signal-pipeline.md) §5. Further feature families to add from
partner data:

| Family | Example features | Source domain |
|---|---|---|
| Attendance | rate over last 14 / 28 days, trend, consecutive absences | `attendance` |
| Internal assessment | submitted count, missing count, mean internal mark, change vs previous term | `academic` |
| LMS activity | logins in last 7 / 28 days, days since last login | `participation` |
| Faculty feedback | count of support-check requests | `faculty_feedback` |
| Fee status | current status (if legally permitted as an input) | finance (restricted) |
| History | previous term outcome, repeat attempts | `academic` |

- **ML-FC-02** The contract is versioned (`feature_contract_version`), lists
  each feature with type, source metric, aggregation, window and missing-value
  policy, and is shared by training and serving code.
- **ML-FC-03** Feature computation applies the same `available_at ≤ cutoff`
  rule as the rules engine.
- **ML-FC-04** Protected and proxy attributes are excluded from inputs (INV-04,
  audit M2). They are joined only in the fairness evaluation step.
- **ML-FC-05** The leakage list is enforced by a test that inspects the
  pipeline's input columns.

## 4. Training pipeline

**Requirement ML-TRN-01 (audit M6):** one training entry point:

```
train --contract <version> --data <snapshot-ref> --config <file>
  1. load snapshot (checksum verified)
  2. build features with cutoff rule
  3. temporal split (train on earlier cohorts, test on later cohort)
  4. grouped CV by student on train
  5. fit baseline (rules-as-features + logistic regression) and any candidates
  6. calibrate on held-out fold (method recorded)
  7. evaluate: discrimination, calibration, capacity metrics, fairness
  8. write candidate artifact + manifest (sha256, metrics, contract, deps lock hash)
  9. register as `candidate`
```

- **ML-TRN-02** Training and serving dependency versions are pinned together;
  the manifest records the lockfile hash (audit M5).
- **ML-TRN-03** Experiments outside the entry point live in an archive folder
  and are not imported by production code.

## 5. Promotion gate

A candidate becomes `approved` only when all checks pass and a named reviewer
signs off in the registry entry.

| Gate | Check |
|---|---|
| Capacity threshold | Threshold chosen from advisor capacity (for example top 10–15% by score). Report precision and recall at that capacity (audit M3). **Open decision:** capacity per campus |
| Calibration | Calibrated on held-out data; reliability curve and Brier score reported. Label in API matches the artifact (audit M4) |
| Fairness | Per-group false-positive and false-negative rates at the chosen threshold; ratio between most- and least-affected group within an agreed bound. **Open decision:** bound and groups |
| Baseline comparison | Beats the rules-only baseline on precision at capacity |
| Stability | Metrics on the latest cohort within an agreed tolerance of CV |
| Leakage | Leakage test passes |
| Reproducibility | Re-running training from the manifest reproduces the artifact hash or metrics within tolerance |

## 6. Serving

| ID | Requirement |
|---|---|
| ML-SRV-01 | At startup, the API loads the `serving` registry entry, downloads the artifact, verifies SHA-256, and refuses to enable ML on mismatch |
| ML-SRV-02 | Model version and hash come from the registry entry, not code constants |
| ML-SRV-03 | Inference runs in a thread or process pool (audit A6) |
| ML-SRV-04 | Requests with missing required features return 422 `ML_FEATURES_UNAVAILABLE` listing missing names; no imputation unless the contract declares it |
| ML-SRV-05 | Every prediction writes `ml_inference_logs` with model version and hash |
| ML-SRV-06 | Batch prediction has a maximum size and rate limit |

### 6.1 ML evidence card

```json
{
  "card_type": "ml_risk_evidence",
  "model_name": "…", "model_version": "…", "model_sha256": "…",
  "feature_contract_version": "…",
  "cutoff": "…",
  "risk_probability": 0.31,
  "threshold": 0.27, "threshold_basis": "top_12_percent_capacity",
  "calibration_method": "isotonic | platt | none",
  "classification": "above_threshold | below_threshold",
  "top_attributions": [{"feature": "…", "value": "…", "contribution": -0.12}],
  "limitations": ["Statistical estimate from past cohorts.", "Not a diagnosis."]
}
```

## 7. Monitoring

| Metric | Source | Frequency |
|---|---|---|
| Score distribution and alert rate | `ml_inference_logs` | Daily |
| Feature missingness | inference requests | Daily |
| Realised precision / recall | inference log joined to later outcomes | Per term |
| Per-group alert and error rates | same, joined with protected attributes in an access-controlled job | Per term |

All monitoring figures come from these tables (audit D2: current
`get_historical_performance_monitoring` returns hardcoded cohort metrics).

## 8. What-if simulation

**Current implementation:** `/ml/simulate-scenario` changes selected features
and re-scores. **Requirement ML-SIM-01:** only features marked
`actionable = true` in the contract can be changed; protected attributes are
never simulation inputs.
