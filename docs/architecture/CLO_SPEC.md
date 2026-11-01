# DISHA CLO insights spec (course learning outcomes)

For the dashboard and backend teammates. The module tells faculty **which course outcomes (COs) and topics students struggle with, and whether that is a teaching gap or a student gap**, so they know what to re-teach. Code: `ml/disha_ml/clo/`. Everything is deterministic and traceable (no ML); every number comes from question-wise marks that colleges already keep for NBA/NAAC. Sample output: `ml/examples/clo_demo_output.json` (synthetic course with planted patterns).

## 1. How to call it

```python
from disha_ml.clo.analyze import analyze_course
payload = analyze_course(tables, "CS201", "2026-odd")   # tables: dict of DataFrames or a folder of <table>.csv[.gz]
payload.to_dict()                                        # plain JSON
```

```bash
python -m disha_ml.clo.analyze --tables <dir> --course CS201 --term 2026-odd [--as-of <day>] [--out f.json] [--no-meko]
python -m disha_ml.clo.synthetic --out <dir>             # demo tables with planted patterns
```

* `as_of` (optional): only assessments due by that day, so the view can be refreshed after each internal exam.
* `--no-meko`: Meko is never contacted (`context.recalled` is `[]`, nothing is stored). Without `MEKO_API_KEY` this is the default behaviour.
* Thresholds live in `CloConfig` (`ml/disha_ml/clo/config.py`) and are echoed in the payload under `config`.
* Status: library and CLI. **Backend to expose** (route proposal in [blueprint 05](../../blueprint/05-api-specification.md) §4.6).

## 2. Input tables

Added to the canonical schema (`ml/disha_ml/rolling/schema.py`); all optional, validated when present. An NBA attainment sheet plus question-wise marks is enough ([blueprint 18](../../blueprint/18-dataset-requirements.md) §10).

| Table | Required | Optional | Notes |
|---|---|---|---|
| `course_outcomes` | `course_id`, `co_id` | `description`, `target_pct` (default 60) | Without it, COs come from `questions` and the target is 60. |
| `questions` | `question_id` (unique), `assessment_id`, `co_id`, `max_marks` (> 0) | `bloom_level` (1-6), `type` (`mcq`/`descriptive`/`rubric`), `correct_option` | `type` defaults to `mcq` when `correct_option` is set. One CO per question. |
| `question_results` | `student_id`, `question_id`, `marks` (0..max) | `selected_option` (MCQ) | A missing row means not attempted, so the student is left out of that question. |
| `topic_feedback` | `student_id`, `course_id`, `term_id`, `day` | `co_id`, `topic` | "Muddiest point" poll. Either `co_id` or free-text `topic`. |
| `teaching_actions` | `course_id`, `term_id`, `co_id`, `day` | `section`, `action` | A recorded re-teach or remedial class. Drives `learnings`. |
| `enrolments` (existing) | | `section` | Added as an optional column. |
| `assessments` (existing) | | `type` | `Exam`/`SEE`/`End...`/`Final...` count as end-semester, everything else as internal (CIE). |

## 3. Payload top level

`schema_version`, `course_id`, `term_id`, `as_of_day`, `n_students`, `sections`, `config`, `co_attainment`, `items`, `bloom`, `misconceptions`, `trends`, `section_comparison`, `muddiest`, `learnings`, `recommendations`, `student_gaps`, `context`, `suppressed`.

Audience: everything except `student_gaps` is **class level (faculty)**. `student_gaps` is marked `"audience": "mentor"` and must only be shown to mentors, never on the class view.

## 4. Insights

Groups are the top and bottom 27% of the class by total score (`top_bottom_frac`). "Reach the target" means a student's CO score is at least the CO's `target_pct`.

### 4.1 CO attainment (`co_attainment[i]`)
* **Question for faculty:** which outcomes did the class not achieve?
* **Definition:** `attainment_pct` = share of students whose CO score (marks earned / max marks on that CO's questions) reaches `target_pct`. Internal and end-semester scores are combined 0.4 / 0.6 (`kind_weights`); when only one kind exists yet, it is used alone. `level`: 3 if attainment >= 70%, 2 if >= 60%, 1 if >= 50%, else 0 (`level_cuts`). `by_kind` gives the attainment per internal / end_sem.
* **Fields:** `co_id`, `description`, `target_pct`, `n_students`, `attainment_pct`, `level`, `mean_pct`, `by_kind`, `p_top`, `p_bottom`, `gap_type`, `questions[]`, `weak_questions[]`.
* **Visual:** horizontal bars per CO with the target line and a level badge (0-3); colour by `gap_type`.
* **Why:** it is the number the accreditation file already asks for, with a reason next to it.

### 4.2 Gap type (`co_attainment[i].gap_type`, `items[i].gap_type`)
* **Question:** is it how I taught it, or are some students not keeping up?
* **Definition** (`p_top`, `p_bottom` = mean score share 0-1 of the top / bottom group): `teaching_gap` when `p_top < 0.5` (even the strongest quarter struggles); `student_gap` when `p_top >= 0.7` and `p_bottom < 0.4`; else `ok`. `insufficient_data` when a group has fewer than `min_group_size` students. The CO value is computed on student-level CO scores; each question gets its own. Thresholds: `teaching_gap_p_top`, `student_gap_p_top`, `student_gap_p_bottom`.
* **Visual:** a chip on each CO bar: red "Teaching gap", amber "Student gap", none for ok.
* **Why:** the fix differs: re-explain the topic for the whole class, or run remedial support for a few.

### 4.3 Question item analysis (`items[i]`)
* **Question:** which questions worked, which were too hard or unclear?
* **Definition:** `difficulty_p` = mean(marks / max); `discrimination` = `p_top - p_bottom`. `flag`: `negative_discrimination` (D < 0: the top group did worse than the bottom, check the key or wording) or `low_discrimination` (D < 0.15, p < 0.9 and gap type ok), both meaning "possibly ambiguous".
* **Fields:** `question_id`, `assessment_id`, `co_id`, `bloom_level`, `type`, `max_marks`, `n`, `difficulty_p`, `p_top`, `p_bottom`, `discrimination`, `gap_type`, `flag`.
* **Visual:** sortable table with a difficulty-vs-discrimination mini bar and the flag as a warning icon.
* **Why:** separates a weak outcome from a badly written question.

### 4.4 Bloom matrix (`bloom.cells[]`, `bloom.insights[]`)
* **Question:** do students manage recall but fail at application?
* **Definition:** `cells[]` = `{co_id, bloom_level, bloom_name, n_students, attainment_pct}` for every CO x Bloom level present (null attainment when under `min_group_size`). An insight is raised when attainment on levels 1-2 (remember/understand) exceeds that on levels 3+ by 20 points (`bloom_gap_pts`) and the upper band is below the level-2 cut (60%). Text example: "CO4: fine on remember/understand (97% reach the target), weak on apply/analyse (0%)".
* **Visual:** heatmap, COs as rows, Bloom levels 1-6 as columns, colour by attainment; insight sentences underneath.
* **Why:** it tells faculty to change the kind of practice (applied problems), not repeat the lecture.

### 4.5 Misconceptions (`misconceptions[]`, MCQ only)
* **Question:** is there one wrong answer many students believe?
* **Definition:** for each MCQ with `selected_option`, the most common wrong option and its `share_pct` of students who answered. `flagged` when the share is >= 30% (`misconception_share`). `top_pct` / `bottom_pct`: share of each group choosing it (null if the group is too small).
* **Visual:** card per flagged question: "Q7: 58% chose B (correct A)", with top vs bottom group bars.
* **Why:** a single shared wrong idea is the cheapest thing to fix in class.

### 4.6 Trend (`trends[i]`)
* **Question:** is the class getting better or worse at this outcome through the term?
* **Definition:** `points[]` = class attainment per assessment in due-day order (internal 1, internal 2, end-semester). `delta_pts` = last minus first; `improving` / `declining` at +-10 points (`trend_delta_pts`), else `steady`; `single_point` with one assessment.
* **Visual:** one line per CO over assessments, with the 60/70% reference lines.
* **Why:** shows whether a re-teach or remedial class helped, before the end-semester exam.

### 4.7 Section comparison (`section_comparison[i]`)
* **Question:** did something work in one section that others can use?
* **Definition:** per CO, `sections[]` = `{section, n_students, attainment_pct, level, trend, delta_pts}`. `insight` is set when sections differ by >= 15 points, worded "See what worked in section X" and including the recorded teaching action there if any. **It never ranks faculty**; show it as shared practice, not a leaderboard. Sections under `min_group_size` students are left out (`suppressed.sections_hidden`).
* **Visual:** grouped bars (sections side by side) per CO.
* **Why:** peer learning without blame.

### 4.8 Muddiest points (`muddiest`)
* **Question:** what do students say they find hardest?
* **Definition:** `items[]` = `{key, label, n_students}` from `topic_feedback`, distinct students per CO or topic, descending; entries with fewer than `min_group_size` students are dropped (`muddiest.suppressed` counts them).
* **Visual:** horizontal count bars next to the CO bars.
* **Why:** the students' own view to cross-check the marks.

### 4.9 Learnings from teaching actions (`learnings[]`)
* **Question:** did the re-teach work?
* **Definition:** for each `teaching_actions` row, attainment on the last assessment due on or before the action day versus the first one after it (section-specific when the action names a section). `improved` when the level rose.
* **Visual:** annotation on the trend line at the action day: "re-teach, level 0 -> 3".
* **Why:** these become Meko course learnings (section 6).

### 4.10 Recommendations (`recommendations[]`)
Deterministic templates with the numbers; `{code, severity, co_id, text, evidence}`, sorted high to low, at most 12.

| code | Example text |
|---|---|
| `RETEACH` | Re-teach CO3 (Recursion): only 2% reached the target; even the top quarter averaged 36% on Q4 - teaching gap |
| `REMEDIAL` | CO2 (Stacks and queues): top students are fine (84%), 16 students below 40% - schedule remedial support |
| `MISCONCEPTION` | Q7 (CO1): 58% chose option B (correct: A) - address this distractor |
| `BLOOM`, `DECLINING`, `AMBIGUOUS_ITEM`, `SECTION`, `MUDDIEST`, `WORKED` | from sections 4.3-4.9 |
| `RECURRING` | CO3 (Recursion) was also at level 0-1 in 2025-odd (recalled from Meko) - a repeat problem |

Visual: a prioritised list at the top of the page, each item linking to its evidence card.

### 4.11 Student gaps (`student_gaps`, **mentors only**)
`{"audience": "mentor", "students": [{student_id, weakest_co, weakest_co_pct, n_cos_below_target, weak_cos[]}]}` with `weak_cos[]` = `{co_id, description, pct, target_pct}`, weakest first; only students below target on at least one CO. Never put this on the class view or in logs; hash ids before logging.

## 5. Privacy

* Class-level outputs hide any group smaller than 5 students (`min_group_size`): a class below 5 returns empty analyses with `suppressed.note`; top/bottom groups, sections, MCQ group shares and muddiest counts are dropped or null below the limit. In recommendations a count under 5 is replaced by "a small group of students".
* Student ids appear only in `student_gaps`.
* Meko memories are aggregates only (section 6).

## 6. Meko course memory and `context`

* `meko_hooks.record_course_learnings(payload)` (run by the CLI after printing, skipped with `--no-meko`) writes short aggregate memories per course, term and section, never student ids or marks. Example: "CS201 2026-odd: CO3 Recursion attainment level 0; teaching gap on Q4; teaching gap on Q5; misconception Q7 option B 58%." Tags: `course-summary`, `course:<id>`, `term:<id>`, `sec:<s>`.
* A `learnings[]` item that improved a level is stored as "CS201 2026-odd sec A: CO3 Recursion improved from level 0 to 3 after re-teach with worked examples (0% to 80%)." with tags `course-learning`, `co:<id>`, `action:<slug>`, `outcome:improved`. When the same course + CO + action has improved in at least 2 terms or sections, the memories are promoted (`memory_promote`, owner/maintainer only) so they surface as shared knowledge.
* **`context.recalled`**: before recommendations are built, `meko_hooks.recall_course_history(course_id)` searches Meko; each hit is returned as `{id, source, text}` where `id` is the Meko memory or document id, `source` is `memory` or `knowledge` (promoted), and `text` is exactly what Meko returned. Show it in the UI as "Recalled from Meko". Nothing is put there that Meko did not return. `context.meko` is `active` or `off`.
* `RECURRING` recommendations are the only place recalled text changes the output (a CO weak both now and in a past term).

## 7. Link to the rolling risk model

`ml/disha_ml/clo/link.py`, called from `score_snapshot` ([INSIGHTS_SPEC.md](INSIGHTS_SPEC.md)): when the CO tables are present, a student below target on a CO gets an extra reason `{group: "co_attainment", text: "Weak on CO3 (Recursion): 35%", effect_pts: 0.0, values: {weakest_co_pct, n_cos_below_target}}` in `students[i].reasons`. Only assessments due by `as_of` are used. Without CO data the payload is unchanged. `effect_pts` is 0 because this is not a model effect: the OULAD model is **not retrained** (OULAD has no question-level data). `weakest_co_pct` and `n_cos_below_target` become model features only once a college supplies CO data and a model is trained on it.
