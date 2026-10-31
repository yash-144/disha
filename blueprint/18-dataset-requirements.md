# 18 · Dataset Requirements

What data the risk-signal pipeline needs, what the first dataset provides, and
how to judge any other dataset.

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

## 2. Columns used (15 inputs, 4 audit, 1 target)

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

**Loading your own file:** the mapping JSON (`python -m kagaz_ml.mapping`)
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
- Synthetic data generated by `ml/kagaz_ml/synthetic.py` is for tests only and
  is never presented as results.
