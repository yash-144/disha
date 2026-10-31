# 18 · Dataset Requirements

What data the risk-signal pipeline needs, what the first dataset provides, and
how to judge any other dataset.

> **Status (2026-11-01).** Sections 1 to 6 cover the datasets of the **legacy
> semester models** (UCI Portugal, UPV Spain). The **primary rolling model**
> uses the canonical, level-agnostic tables in section 7, trained on OULAD
> (section 8). Section 9 lists what a college must provide.

## 1. First dataset: UCI "Predict Students' Dropout and Academic Success"

| Item | Value (from the dataset description) |
|---|---|
| Source | UCI Machine Learning Repository; also mirrored on Kaggle |
| Institution | One higher-education institution in Portugal |
| Rows | 4,424 students |
| Columns | 36 attributes + target |
| Target | Graduate, Dropout, Enrolled (still enrolled after normal course length) |
| Licence | CC BY 4.0 (check the copy you download) |
| Grade scales | Semester grades 0–20; admission and previous qualification grades 0–200 |
| Has | Prior grades, course, per-semester curricular-unit counts and grades for semesters 1–2 |
| Lacks | Attendance, internal assessment marks, LMS activity, enrolment year, names |

The training run prints the actual row count and outcome counts; check them
against the description of the copy you downloaded.

Repository copy: `ml/data/raw/data_raw.csv` (as downloaded) and
`ml/data/processed/data.csv` (header fixes only; see
`docs/audit/anomaly_report.md`). Measured on the processed file: 4,424 rows;
Graduate 2,209, Dropout 1,421, Enrolled 794; no missing values; no duplicates.
Data issues handled by the loader:
- 180 students (all in course 171) have every curricular-unit field 0 in both
  semesters, including 75 graduates. This is treated as "no semester record",
  so these students are assessed only at admission (`cp0`).
- 3 students have more semester-2 subjects without evaluation than enrolled;
  the value is capped at enrolled.

### Second dataset: UPV Spain (time-based check)

*StudentDropoutDataset*, Universitat Politècnica de València, Zenodo 2025
(https://doi.org/10.5281/zenodo.17239943), CC BY 4.0. Verified: open download,
39,364 students, 464,739 student-course-year rows, years 2018, 2021, 2022.
DISHA keeps first-year bachelor's students: 8,999 students, 1,144 dropouts,
converted by `ml/disha_ml/converters/upv.py` into
`ml/data/processed/upv_first_year.csv`. It adds campus Wi-Fi days as an
attendance stand-in (2021, 2022) and a `cohort_year` for training on earlier
intakes and testing on a later one. Mapping, caveats and results:
`ml/README.md` §26.

## 2. Columns used (UCI: 15 inputs, 4 audit, 1 target)

Two optional inputs were added later: `s1_attendance` and `s2_attendance`
(attendance %, or days present), plus `cohort_year` for a time-based test. They
are used when a dataset has them and left out otherwise.

| Canonical name | Source header | Role |
|---|---|---|
| `prev_qual_grade` | Previous qualification (grade) | Input (all checkpoints) |
| `admission_grade` | Admission grade | Input (all) |
| `course` | Course | Input (all), categorical |
| `s1_credited` … `s1_without_eval` | Curricular units 1st sem (credited / enrolled / evaluations / approved / grade / without evaluations) | Input from `cp1` |
| `s2_credited` … `s2_without_eval` | Curricular units 2nd sem (same six) | Input at `cp2` |
| `gender` | Gender | Audit only |
| `age_at_enrollment` | Age at enrollment | Audit only |
| `displaced` | Displaced | Audit only |
| `special_needs` | Educational special needs | Audit only |
| `target` | Target | Label |

All other 17 columns are dropped at load time.

## 3. Minimum requirements for any training dataset

| # | Requirement | Why |
|---|---|---|
| 1 | One row (or set of rows) per student, with a stable pseudonymous id | Linking records |
| 2 | A **known outcome** per student (dropout / pass / fail / on time) recorded after the prediction point | No outcome → nothing to learn from |
| 3 | Inputs dated so that "known at checkpoint" can be decided | Prevents using future data |
| 4 | At least ~1,000 students and ~150 positive outcomes per checkpoint | Below this, an 85%-precision cutoff with ≥ 30 students is rarely reachable |
| 5 | At least two cohorts (years) for a time-based test | Honest estimate of performance on next year's students |
| 6 | Course or programme identifier | Course difficulty differs |
| 7 | Protected attributes held separately, if available | Fairness check |
| 8 | Lawful basis and anonymisation (see §6) | Legal and ethical use |

## 4. Mapping to Indian university data

| Pipeline field | UCI source | Typical Indian university source |
|---|---|---|
| Prior grades | Previous qualification / admission grade | Class 12 percentage, entrance exam score / rank |
| Course | Course code | Programme / branch |
| Subjects enrolled | Curricular units enrolled | Subjects registered in the semester |
| Subjects evaluated | Curricular units evaluations | Exams appeared |
| Subjects without evaluation | Curricular units without evaluations | Absent / detained from exam |
| Subjects passed | Curricular units approved | Subjects cleared (no backlog) |
| Semester grade | Curricular units grade (0–20) | SGPA (0–10) or mean marks; convert scale in the mapping |
| Credited | Curricular units credited | Credit transfer / exemptions |
| Outcome | Target | Dropped out / detained / backlog at year end / graduated on time |
| *(not in UCI)* Attendance | — | Attendance % per subject; rules today, model feature once outcomes exist |
| *(not in UCI)* Internal marks | — | Mid-semester / internal assessment marks; enables a mid-semester checkpoint |

With attendance and internal marks, an extra **mid-semester checkpoint**
becomes possible, which flags students weeks earlier than `cp1`.

**Loading your own file:** the mapping JSON (`python -m disha_ml.mapping`)
connects your headers to the fields above, maps your outcome values to
Dropout / Graduate / Enrolled, and sets `grade_scale` (10 for SGPA, 100 for
percentage) so grades are rescaled to the 0–20 scale the rules use. Attendance
and internal marks are not yet model inputs in the code; adding them means new
canonical fields in `data.py` and features in `features.py`.

## 5. Checklist for evaluating a candidate dataset

- [ ] Has an outcome column, and its meaning is documented.
- [ ] Outcome is measured after the inputs.
- [ ] Row count and positive count meet §3 item 4.
- [ ] Column meanings and scales are documented.
- [ ] No column is a disguised outcome (for example "final result", "date of
      leaving", "status at year end").
- [ ] Licence permits the intended use.
- [ ] Contains no direct identifiers, or they can be removed before training.
- [ ] Missing-value meanings are known (for example "0 = no grade").

## 6. Privacy rules for real student data

- Remove names, roll numbers, phone numbers and emails before training;
  replace with a pseudonymous id; keep the mapping table separately with
  restricted access.
- Names may appear only in the demo UI, never in training files, model inputs,
  logs or reports.
- Protected attributes (gender, caste/category, religion, region, disability,
  age, family income) are never model inputs; they are used only in the
  fairness check, in a restricted step.
- Real student data needs a data-sharing agreement with the institution and a
  review under India's DPDP Act 2023 before use.
- Synthetic data generated by `ml/disha_ml/synthetic.py` is for tests only and
  is never presented as results.

## 7. Canonical input schema (rolling model)

One schema for school, UG year 1 to 4 and PG. Marks are percentages 0 to 100;
every `day` is relative to term start (day 0 = start; negative = before).
Validation: `ml/disha_ml/rolling/schema.py`. Column semantics and examples:
[`docs/architecture/INSIGHTS_SPEC.md`](../docs/architecture/INSIGHTS_SPEC.md) §2.

| Table | Required | Optional |
|---|---|---|
| `students` (whole table optional) | `student_id` | `program_level` (school / ug / pg), `year_of_study`, `tenth_pct`, `twelfth_pct`, `entrance_pct`, `prior_education_ord`; audit-only `gender`, `region`, `imd_band`, `disability`, `age_band` |
| `enrolments` | `student_id`, `term_id`, `course_id`, `term_length_days` | `term_start`, `outcome` (training only: Pass, Distinction, Fail, Withdrawn), `prev_attempts`, `credit_load` |
| `assessments` | `assessment_id`, `course_id`, `term_id`, `due_day` | `weight`, `type` (`Exam` rows never trigger a snapshot) |
| `results` (optional) | `student_id`, `assessment_id`, `submitted_day` | `score_pct` (empty = not marked) |
| `activity` (optional) | `student_id`, `course_id`, `term_id`, `day`, `count` | LMS clicks or attendance marks per student per day |
| `withdrawals` (optional) | `student_id`, `course_id`, `term_id`, `day` | |

* One enrolment is `(student_id, course_id, term_id)` and must be unique.
* Baseline: `tenth_pct`, `twelfth_pct`, `entrance_pct` are averaged when present;
  if the whole cohort lacks them, `prior_education_ord` (0 to 4) is used.
* Audit columns are never model inputs.
* A snapshot at day t uses only rows dated at or before t.

## 8. Third dataset: OULAD (rolling model)

Open University Learning Analytics Dataset: anonymised UK distance-learning data,
about 32,600 enrolments, 22 course presentations in 4 terms (2013B, 2013J,
2014B, 2014J), 10.6M daily LMS click rows, outcomes Pass / Distinction / Fail /
Withdrawn. Licence CC BY 4.0 (Kuzilek, Hlosta, Zdrahal, *Scientific Data* 4,
170171, 2017). The official download link no longer serves the zip, so the copy
used is the Internet Archive capture of it; URL, byte size and SHA-256 are in
`ml/data/raw/oulad/SOURCE.md`. The raw CSVs are git-ignored. The converter is
`python -m disha_ml.converters.oulad`.

Why it fits: it has dated assessments with scores, dated submissions, daily
activity and dated withdrawals, which the semester datasets lack. Its limits:
no 10th/12th/entrance marks (the education level stands in as
`prior_education_ord`), UK, distance learning, and a high at-risk base rate
(41.9% of training snapshot rows, 35.4% of test rows).

## 9. What a college must provide

For the rolling model to score a campus, the backend (or an export) supplies the
six canonical tables.

| Need | Why | Minimum |
|---|---|---|
| Course-terms with a length in days | Term fraction, next-check dates | `enrolments.term_length_days` |
| Assessment calendar with due days | Snapshots are taken at each due date | `assessments.due_day` for every graded component; mark exams `type = Exam` |
| Marks as percentages | Score features | `results.score_pct` (convert SGPA or grades to 0 to 100) |
| Submission dates | Missed and late counts | `results.submitted_day`; a missing row means not submitted |
| Daily engagement | Engagement features | `activity` (LMS clicks, attendance marks); optional but strongly advised |
| Withdrawal dates | Excludes already-withdrawn students; lead-time measurement | `withdrawals` |
| Entry baseline | Baseline gap and rank | 10th, 12th or entrance percentages, or an ordinal education level |
| Final outcomes for past terms | Training labels | `enrolments.outcome` (Pass, Distinction, Fail, Withdrawn) for at least one full earlier term, with a later term to test on |
| Pseudonymous `student_id` | Linking; Meko hashing | stable across tables and terms |

Privacy rules in §6 apply unchanged. Demographic columns are optional and are
used only for fairness slices. Checklist in §5 still applies; add: at least two
terms (one to train, one to test) and enough at-risk enrolments for a HIGH
cutoff to be reachable (§3 item 4).

## 10. Course-outcome (CLO) data

Optional, for the CLO insights ([`docs/architecture/CLO_SPEC.md`](../docs/architecture/CLO_SPEC.md)). Colleges already keep this for NBA/NAAC, so there is no answer-sheet scanning: an **NBA attainment sheet plus question-wise marks from the ERP is enough**.

| Table | Columns (required first) | From the college's existing records |
|---|---|---|
| `course_outcomes` | `course_id`, `co_id`; `description`, `target_pct` (default 60) | the CO list and target in the course file |
| `questions` | `question_id`, `assessment_id`, `co_id`, `max_marks`; `bloom_level` (1-6), `type` (mcq/descriptive/rubric), `correct_option` | the question-to-CO (and Bloom) mapping of each paper |
| `question_results` | `student_id`, `question_id`, `marks`; `selected_option` (MCQ) | question-wise marks entered in the ERP |
| `topic_feedback` | `student_id`, `course_id`, `term_id`, `day`; `co_id` or `topic` | optional "muddiest point" poll |
| `teaching_actions` | `course_id`, `term_id`, `co_id`, `day`; `section`, `action` | optional log of re-teach / remedial classes |
| `enrolments.section` | optional column | class section |

Mark internal (CIE) and end-semester (SEE) assessments through `assessments.type` (`Exam` or a name containing `SEE`/`End`/`Final` is end-semester). Privacy rules in §6 apply; class-level views hide groups under 5 students. The OULAD model has no question-level data, so these tables are not used to train it.
