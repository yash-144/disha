# DISHA insights spec (rolling risk model)

For the dashboard and backend teams. Source of truth: `ml/disha_ml/rolling/` (`insights.py` is the JSON schema).
The semester models (`cp0`, `cp1`, `cp2`) are unchanged and are now the "legacy semester models".

## 1. How to call it

```python
from disha_ml.rolling.score import score_snapshot
payload = score_snapshot(tables, as_of=120)      # -> InsightsPayload; payload.to_dict() / payload.to_json()
```

- `tables`: dict of pandas DataFrames in the canonical schema (section 2), or a folder holding `<table>.csv` / `<table>.csv.gz`.
- `as_of`: day number since term start (day 0 = term start). It applies to every course-term in `tables`.
- Model: `ml/artifacts_rolling/` (`model.joblib`, `manifest.json`, `report.md`), loaded by default; pass `bundle=load_bundle(path)` to override.
- CLI: `python -m disha_ml.rolling.score --tables <dir> --as-of 120 [--model <dir>] [--out file.json] [--no-meko]`. Prints JSON, or writes `--out`.
- Train: `python -m disha_ml.rolling.train --data ml/data/raw/oulad --no-meko`.
- Scoring all 32k OULAD enrolments takes about 15 s on a laptop, so score per course-term or per day, not per click.
- When to call: after each batch of marks reaches the ERP (one call per assessment due date) and optionally weekly for engagement.
- Meko: after scoring, the CLI calls `meko_hooks.record_assessment_updates(payload.to_dict())`. It writes only for students whose tier changed or who had a drift event, with hashed ids; `--no-meko` disables it.
- Students are keyed by the `student_id` the caller supplied (not hashed in the payload; hash before logging elsewhere).

## 2. Canonical input schema

Level-agnostic (school, UG year 1-4, PG). All marks are percentages 0-100. All `day` values are days relative to term start. Validation: `disha_ml.rolling.schema.validate`.

| Table | Required columns | Optional columns |
|---|---|---|
| `students` (table optional) | `student_id` | `program_level` (school/ug/pg), `year_of_study`, `tenth_pct`, `twelfth_pct`, `entrance_pct`, `prior_education_ord`, audit-only: `gender`, `region`, `imd_band`, `disability`, `age_band` |
| `enrolments` | `student_id`, `term_id`, `course_id`, `term_length_days` | `term_start` (ISO date, gives calendar dates), `outcome` (training only: Pass, Distinction, Fail, Withdrawn), `prev_attempts`, `credit_load` |
| `assessments` | `assessment_id`, `course_id`, `term_id`, `due_day` | `weight`, `type` (TMA, CMA, Exam, ...; `Exam` rows never trigger a snapshot) |
| `results` (optional) | `student_id`, `assessment_id`, `submitted_day` | `score_pct` (empty = missing) |
| `activity` (optional) | `student_id`, `course_id`, `term_id`, `day`, `count` | LMS clicks, or attendance marks, per student per day |
| `withdrawals` (optional) | `student_id`, `course_id`, `term_id`, `day` | |

Notes
- One enrolment = `(student_id, course_id, term_id)`; it must be unique in `enrolments`.
- Baseline: `tenth_pct`/`twelfth_pct`/`entrance_pct` are averaged when present. If the whole cohort has none, `prior_education_ord` (0-4 ordinal) is used instead. In OULAD it stands in for 10th/12th marks (`highest_education`: No Formal quals 0 ... Post Graduate 4).
- Sensitive demographics (gender, region, imd_band, disability, age_band) are never model inputs. They only feed fairness audits.
- A snapshot at day t uses only rows dated <= t. Enrolments withdrawn at or before t get no row at all.
- Converter for OULAD: `python -m disha_ml.converters.oulad`.

## 3. Snapshots, label, features

- Snapshot rows exist for every non-exam assessment due date, plus fixed points at 10%, 25%, 50%, 75% of the term, plus `as_of` when scoring. Training label `at_risk` = final outcome is Fail or Withdrawn.
- Result counting: an assessment counts at day t when `due_day <= t`; its result counts when `submitted_day <= t`.
- Features (23): `mean_score`, `weighted_score`, `last_score`, `score_change`, `score_slope`, `standing_pct`, `gap_to_median`, `share_submitted`, `n_missed`, `n_late`, `consecutive_misses`, `missed_last3`, `activity_vs_median`, `engagement_ratio`, `days_since_activity`, `term_frac`, `assessment_idx`, `baseline_rank`, `baseline_gap`, `prev_attempts`, `credit_load`, `program_level_code`, `year_of_study`.
- Cohort-relative values (`standing_pct`, `gap_to_median`, `activity_vs_median`, `baseline_rank`) are computed within the same course and term over students still active at t.
- `engagement_ratio` = (clicks per day in the last 14 days) / (the student's own clicks per day from day 0 to t-14); needs t >= 27; clipped to 0-10.

## 4. Payload top level

```
schema_version  "1.0"
as_of_day       int
model           {bundle_version, trained_terms, cutoffs{high,medium,watch}}
n_students      int
students[]      StudentInsight   (section 5)
cohorts[]       CohortInsight    (section 6)
data_drift      DriftReport      (section 7)
```

Tiers (`ml/disha_ml/signal.py`): HIGH when p >= HIGH cutoff; MEDIUM when p is between the MEDIUM and HIGH cutoffs and at least one academic rule fires; WATCH otherwise above the WATCH cutoff or in the MEDIUM band without a rule; ON_TRACK below. HIGH and MEDIUM are "signals". A capacity cap keeps signals to at most 25% of the active students of each course-term at that day; extra ones become WATCH. Cutoffs come from out-of-fold probabilities at precision targets 0.85 / 0.70 / 0.50.
Academic rules (any one counts): missed >= 2 of the last 3 assessments; mean score <= 15 points below the class median; engagement ratio <= 0.5; last score >= 10 points below the previous; percentile gap to baseline <= -25; >= 2 consecutive misses.

## 5. Per-student insights (`students[i]`)

Each entry is one enrolment still active at `as_of`. Identity: `student_id`, `course_id`, `term_id`, `as_of_day`, `last_assessment` (label such as TMA3, the latest one due by as_of).

| Insight | Question for the mentor | Definition | JSON path | Visual | Why it matters |
|---|---|---|---|---|---|
| Risk probability and tier | How likely is this student to fail or withdraw, and how urgent is it? | Calibrated probability (isotonic) that the final result is Fail or Withdrawn, given data to as_of. Tier per section 4. | `risk.probability`, `risk.tier`, `risk.signal` | Card with tier badge and percentage | The one number and colour mentors triage by. |
| Risk change | Is it getting better or worse since the last marks? | `delta` = p - previous snapshot's p. `direction`: `up` when delta >= +0.05, `down` when <= -0.05, else `steady`; `new` when there is no previous snapshot. | `risk.previous_probability`, `risk.previous_tier`, `risk.previous_day`, `risk.delta`, `risk.direction` | Arrow chip beside the card | Movement matters more than level for catching sudden slips. |
| Risk history | How has risk moved through the term? | p and tier at every snapshot up to as_of (assessment days and fixed points). | `history[]` = `{day, probability, tier}` | Sparkline coloured by tier | Shows whether a high tier is new or long-standing. |
| Top reasons | Why is this student flagged? | Up to 3 feature groups whose replacement by a typical student's values lowers risk by >= 2 points (ablation, `explain.group_contributions`), worded from the student's own numbers. Groups: score_level, score_trend, submissions, engagement, baseline, load_history. | `reasons[]` = `{group, text, effect_pts, values}` | Ranked list with effect bars | Turns a score into something a mentor can say to the student. Examples: "Average 41%, 23 points below the class median"; "Missed 2 of the last 3 assessments"; "Online activity down 64% over the last 2 weeks vs their own earlier rate"; "Score fell 18 points since the previous assessment"; "Performing below their entry baseline". |
| What is on track | What is going well? | Up to 2 groups that lower risk by >= 2 points, with positive wording (same ablation). | `on_track[]` (same shape as reasons; `effect_pts` negative) | Green chips | Keeps the conversation balanced; gives something to praise. |
| Drift events | Did something just change? | Evaluated at as_of against the previous snapshot. `SCORE_DROP`: a new mark arrived and `score_change <= -15`. `ENGAGEMENT_COLLAPSE`: `engagement_ratio <= 0.4` now and not at the previous snapshot. `FIRST_MISSED_SUBMISSION`: `n_missed >= 1` now and 0 before. | `drift_events[]` = `{code, day, text, values}` | Timeline markers / alert chips | Sudden changes often precede formal risk and are the best prompt for a check-in. |
| Next check | When should we look again? | The next assessment due after as_of (exams included). `date` only if `enrolments.term_start` is given. | `next_check` = `{day, date, assessment_id}` | Date chip | Tells the mentor when new evidence arrives. |
| Snapshot facts | What are the headline numbers? | `mean_score`, `class_median_score`, `standing_pct`, `gap_to_median`, `share_submitted`, `n_missed`, `activity_vs_median`, `engagement_ratio`, `term_frac`. | `snapshot{}` | Small stat row | Lets the UI show the evidence beside the reasons without a second query. |

## 6. Cohort / course insights (`cohorts[i]`, one per course-term)

| Insight | Question | Definition | JSON path | Visual | Why |
|---|---|---|---|---|---|
| Counts | How big is the cohort? | `n_enrolled`, `n_active` (not withdrawn by as_of), `n_withdrawn`. | `n_enrolled`, `n_active`, `n_withdrawn` | Numbers | Context for every share below. |
| Risk distribution | How is the cohort spread across tiers? | Count and share of active students per tier at as_of. | `tier_distribution.{HIGH,MEDIUM,WATCH,ON_TRACK}.{n,share}` | Stacked bar | Shows workload and whether the cap bites. |
| At-risk share per course | Which courses have the most students in trouble? | `at_risk_share` = (HIGH + MEDIUM) / active; `mean_risk` = mean probability. | `at_risk_share`, `mean_risk` | Ranked bar across `cohorts[]` | Directs department-level attention. |
| Early-warning hotspot | Where do struggling students first fall behind? | Among currently signalled students, the first assessment (by due day) each missed or scored 10+ points below the class median on it; the hotspot is the assessment with most such first falls. | `hotspot` = `{assessment_id, label, due_day, n_students, share_of_at_risk}` (null if none); `hotspot_breakdown[]` = `{assessment_id, label, due_day, n_students}` | Bar per assessment, hotspot highlighted | Points to the module element (or timing) where support helps most. |
| Time-to-risk curve | How fast do students become flagged? | At each snapshot day up to as_of: `signalled_share` (signalled / enrolled) and `cumulative_signalled_share` (ever signalled by that day / enrolled). | `time_to_risk[]` = `{day, n_active, signalled_share, cumulative_signalled_share}` | Line chart over days | Shows whether risk shows up early or late in the term. |

## 7. Model / data drift (`data_drift`)

| Field | Definition |
|---|---|
| `features[]` = `{feature, psi, status}` | PSI per feature (10 reference quantile bins plus a missing bin; eps 1e-4) between the training cohorts at the nearest fixed term fraction (10/25/50/75%) and the rows scored at as_of. Status: `ok` < 0.1, `watch` 0.1-0.2, `shift` > 0.2. Excluded: `term_frac`, `assessment_idx`, `baseline_rank`. |
| `max_psi`, `retrain_recommended` | `retrain_recommended` is true when any feature has PSI > 0.2. |
| `note` | "PSI > 0.2 on ...; consider retraining." or "No feature shifted beyond the PSI threshold." |
| `reference_rows`, `current_rows` | Row counts compared. |

Visual: table sorted by PSI with a status colour; a banner when `retrain_recommended`. Why it matters: marks and engagement habits change by term, department and level; a drifted input means the probabilities are less trustworthy.

## 8. Meko academic-story memories

Each scored assessment now also feeds the student's Meko journey: `record_assessment_updates` posts an `assessment_update` turn for every scored student-assessment (not only changed tiers), plus `tier_change` and `drift_event` turns, into that student's own conversation `journey:<hashed id>`. Details, event types, privacy and quota: [MEKO_INTEGRATION.md, "Student academic journey"](MEKO_INTEGRATION.md#student-academic-journey). Ids are hashed (needs `MEKO_PII_SALT`); exact marks stay in the canonical tables.

## 9. Course-outcome (CO) reasons

When the optional CO tables (`questions`, `question_results`, ...) are supplied, `students[i].reasons` may end with `{group: "co_attainment", text: "Weak on CO3 (Recursion): 35%", effect_pts: 0.0, values: {weakest_co_pct, n_cos_below_target}}` for a student below target on a CO (only assessments due by `as_of`). `effect_pts` is 0: it is context, not a model effect (the model is not trained on CO data). Without CO data nothing changes. Class-level CO insights and their payload: [CLO_SPEC.md](CLO_SPEC.md).
