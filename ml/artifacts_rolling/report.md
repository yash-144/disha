# Rolling risk model report

Dataset: OULAD (CC BY 4.0), see data/raw/oulad/SOURCE.md. Train terms ('2013B', '2013J', '2014B'), test terms ('2014J',).
Rows: train 173,960 (17,488 students, base rate 41.9%), test 80,411 (8,931 students, base rate 35.4%). One row = one student in one course-term at one snapshot day.

## Test metrics (all snapshots of the held-out term)

| ROC-AUC | PR-AUC | Brier | ECE | Accuracy | Majority baseline |
|---|---|---|---|---|---|
| 0.857 | 0.794 | 0.145 | 0.037 | 79.0% | 64.6% |

Rules-only score AUC for comparison: 0.689.

## How early can we catch them (AUC at a fraction of the term)

| Term elapsed | Rows | Base rate | ROC-AUC |
|---|---|---|---|
| 10% | 9,223 | 40.8% | 0.727 |
| 25% | 8,746 | 37.6% | 0.809 |
| 50% | 8,160 | 33.1% | 0.881 |
| 75% | 7,648 | 28.6% | 0.933 |

## Lead time

Withdrawn students with at least one snapshot: 1,768. Signalled (HIGH or MEDIUM) before withdrawing: 1,246 (70.5%). Days between first signal and withdrawal: median 54.0, interquartile 25.25 to 112.0.

## Tiers (test; capacity cap applied per course, term and day)

Cutoffs on out-of-fold probability: HIGH 0.554 (precision target met at 85.0%), MEDIUM 0.333 (precision target met at 70.0%), WATCH 0.089 (precision target met at 50.0%). Capacity cap 25% of active students.

| Tier | n | Share | Precision | Recall |
|---|---|---|---|---|
| HIGH | 19,085 | 23.7% | 81.7% | 54.7% |
| MEDIUM | 957 | 1.2% | 45.6% | 1.5% |
| WATCH | 44,090 | 54.8% | 26.9% | 41.6% |
| ON_TRACK | 16,279 | 20.2% | 3.7% | 2.1% |
| SIGNAL (HIGH+MEDIUM) | 20,042 | 24.9% | 79.9% | 56.2% |
| EVER SIGNALLED (per student) | 4,515 | 48.6% | 67.5% | 79.6% |

## Overfitting check

| Train AUC | CV AUC (grouped by student) | Test AUC | Train-CV gap | CV-test gap |
|---|---|---|---|---|
| 0.894 | 0.883 | 0.857 | +0.011 | +0.026 |

14.3% of test rows belong to students who also appear in a training term (repeaters). Test AUC on unseen students only: 0.854.

## Model size

44,340 parameters = 21,000 tree split nodes + 22,500 leaves + 840 isotonic calibration points, over 1,500 trees in 5 calibration folds (averaged at prediction time). Artifact 4.09 MB; trained in 101.2s.

## Fairness slices (signal rate and false-positive rate by group; demographics are NOT model inputs)

**gender** (FPR max/min ratio: 1.2)

| Group | n | Signal rate | FPR | Miss rate |
|---|---|---|---|---|
| F | 33,135 | 23.6% | 8.6% | 46.3% |
| M | 47,276 | 25.8% | 7.1% | 42.2% |

**region** (FPR max/min ratio: 1.87)

| Group | n | Signal rate | FPR | Miss rate |
|---|---|---|---|---|
| East Anglian Region | 7,447 | 22.5% | 8.3% | 47.4% |
| East Midlands Region | 5,447 | 22.1% | 7.2% | 47.2% |
| Ireland | 3,717 | 22.1% | 5.6% | 45.5% |
| London Region | 7,154 | 26.5% | 8.0% | 41.4% |
| North Region | 4,662 | 21.0% | 7.2% | 47.9% |
| North Western Region | 6,446 | 30.0% | 8.6% | 37.7% |
| Scotland | 11,279 | 25.7% | 5.8% | 44.0% |
| South East Region | 5,148 | 24.4% | 10.5% | 45.2% |
| South Region | 7,335 | 21.8% | 7.4% | 45.6% |
| South West Region | 5,929 | 24.3% | 7.4% | 43.7% |
| Wales | 5,761 | 29.3% | 8.7% | 42.1% |
| West Midlands Region | 5,577 | 26.5% | 8.0% | 43.0% |
| Yorkshire Region | 4,509 | 26.1% | 9.2% | 42.0% |

**imd_band** (FPR max/min ratio: 2.02)

| Group | n | Signal rate | FPR | Miss rate |
|---|---|---|---|---|
| 0-10% | 6,959 | 30.7% | 9.3% | 41.4% |
| 10-20 | 7,774 | 31.2% | 9.6% | 39.3% |
| 20-30% | 8,351 | 28.6% | 7.5% | 40.5% |
| 30-40% | 8,520 | 26.1% | 8.4% | 42.5% |
| 40-50% | 7,996 | 26.1% | 8.9% | 42.3% |
| 50-60% | 8,041 | 24.8% | 7.7% | 43.8% |
| 60-70% | 7,769 | 22.5% | 7.6% | 46.9% |
| 70-80% | 7,702 | 23.3% | 6.4% | 44.4% |
| 80-90% | 7,235 | 20.4% | 7.9% | 51.6% |
| 90-100% | 6,632 | 18.8% | 6.1% | 47.9% |
| unknown | 3,432 | 15.1% | 4.8% | 51.4% |

**disability** (FPR max/min ratio: 1.21)

| Group | n | Signal rate | FPR | Miss rate |
|---|---|---|---|---|
| N | 73,282 | 24.0% | 7.6% | 44.7% |
| Y | 7,129 | 34.5% | 9.2% | 36.2% |

**age_band** (FPR max/min ratio: 1.94)

| Group | n | Signal rate | FPR | Miss rate |
|---|---|---|---|---|
| 0-35 | 55,526 | 26.8% | 8.2% | 41.6% |
| 35-55 | 24,123 | 20.8% | 6.8% | 49.5% |
| 55<= | 762 | 18.5% | 4.2% | 46.1% |

## Features

mean_score, weighted_score, last_score, score_change, score_slope, standing_pct, gap_to_median, share_submitted, n_missed, n_late, consecutive_misses, missed_last3, activity_vs_median, engagement_ratio, days_since_activity, term_frac, assessment_idx, baseline_rank, baseline_gap, prev_attempts, credit_load, program_level_code, year_of_study
