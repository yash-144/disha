# DISHA submission answers

Ready-to-paste blocks. Each answer stands alone.

---

## 1. Project Title

DISHA: Catch struggling students weeks earlier, and make sure every warning ends in action

---

## 2. What problem does your project solve?

Students rarely fail or drop out suddenly. They miss a submission, go quiet online, and their marks slip. By the time a mid-term grade or an attendance report shows it, many have already left. In the open Open University dataset we used, 46.6% of students who withdrew with a recorded date did so before the first assessment was even due. A system that waits for marks cannot see them.

The second problem is what happens after a warning. Most early-warning tools stop at a risk score. A score with no owner, no deadline and no recorded outcome becomes one more dashboard nobody opens. Staff cannot tell which alerts are reliable, and nobody learns which support actually helped.

Universities everywhere lose a large share of entrants. In the United States, about one in four full-time first-time undergraduates did not return to the same institution for a second year (NCES, fall 2020 cohort). UNESCO reports that global higher-education enrolment rose from 19% to 44% between 2000 and 2024 while the first-degree graduation ratio rose only from 17% to 27%.

DISHA addresses both gaps. It scores every student in every course each week, from marks, submissions and online activity, and explains why in plain words. Then it turns the strongest warnings into cases with one owner, one deadline, one intervention and a recorded outcome. The goal is simple: no alert without action.

---

## 3. The Solution and Architecture

**How it works.** A campus uploads marks, assessment due dates, submissions and weekly learning-platform activity through the admin portal. Files are validated and every import is versioned. Each week the risk model scores each student in each course as of that day of term. It gives a probability, a tier and the top reasons. The tiers are shown to users as: Needs help now, Needs a closer look, Keep an eye on, and On track.

**The risk model in plain words.** It asks one question: how likely is this student to fail or withdraw from this course? It uses 23 inputs in six groups: marks level and trend, submissions (missed, late, in a row), online activity compared with the class, entry background, and course load. Gender, region, deprivation, disability and age are never inputs. They are used only to audit fairness. The model is scikit-learn gradient boosting with isotonic calibration, so "80%" means about 80 in 100. It was trained on real Open University data (17,488 students, three terms) and tested on a fourth term it had never seen.

**Held-out results.** ROC-AUC 0.857 and PR-AUC 0.794. The strongest alerts (Needs help now) are 81.7% precise. Of students who later withdrew, 70.5% were flagged first, with a median of 54 days of warning (middle half: 25 to 112 days). About 8 in 10 struggling students were flagged at some point, and about 7 in 10 flags were correct. These are alert precision figures, not accuracy.

**From score to action.** A campus policy decides which tiers open a case and caps new cases per run. Each case moves through a 14-state workflow with versioned edits, deadlines and escalation. Every step is written to an append-only audit chain with hash verification.

**Four portals.** Admin (campus overview, model health, data import, policy, audit). Counsellor (caseload, notes, follow-ups, sessions). Faculty (their classes and flagged students). Student (own courses, weekly check-in, support requests).

**Meko (optional).** An agent-memory service that remembers which interventions actually worked for students with the same pattern (an outcome playbook), each student's story over the term, every human decision on a flag, and model experiments. Student ids are hashed and a guard strips personal data. DISHA works without it.

**Flow**
- Campus data (marks, submissions, activity) -> import and validation
- -> weekly risk model -> tier plus reasons
- -> campus policy -> suggested case
- -> counsellor review -> owner, deadline, intervention
- -> outcome recorded -> audit chain -> playbook (Meko)

**Stack**
- Web: React 19, TypeScript, Vite, Tailwind, TanStack Query
- API: FastAPI, async SQLAlchemy, Alembic, Pydantic
- Database: Supabase PostgreSQL
- Sign-in: Supabase Auth with Google, verified and exchanged for a short-lived DISHA token. Roles come from the server, never the client
- ML: scikit-learn model bundle, checksum checked on load
- Data access: role-scoped, with small groups (under 5) hidden in analytics

**Honest note on the demo.** The dashboards show a sample campus with invented students, scored by the real model. We have not deployed DISHA or run a pilot. A real campus must monitor drift and retrain on its own history, because the model was trained at a UK distance-learning university.

---

## 4. Public GitHub Repository Link

https://github.com/yash-144/disha

---

## 5. What do you think should be the success metrics of the project?

1. **Warning lead time.** Days between the first flag and the day a student leaves a course. Measured on each campus's own scoring runs. Already demonstrated on held-out open data: median 54 days (middle half 25 to 112). Target on a real campus: median of 3 weeks or more. Needs a real term.
2. **Alert precision (HIGH tier).** Share of "Needs help now" flags where the student really ended up failing or withdrawing. Already demonstrated: 81.7% on the unseen term. Target on a real campus: 70% or more after retraining. Needs a real term to confirm, because the model came from a different university.
3. **Coverage of struggling students.** Share of students who failed or withdrew who were flagged at some point. Already demonstrated: about 8 in 10 (79.6%). Needs a real term.
4. **Flag-to-action rate and speed.** Share of suggested cases reviewed within the deadline, and median hours from flag to first student contact. Measured from the case workflow and audit chain. The measurement is built in. The numbers need a real term. No baseline claimed.
5. **Outcome improvement for supported students.** Share of closed cases recorded as improved, compared with similar flagged students who received no support. This is the metric that shows whether the system helps. It is not demonstrated. It needs a real term and a fair comparison group.
6. **Course retention and completion.** Withdrawal and failure rate per course before and after adoption. This is the end goal DISHA aims at. We make no claim that it reduces dropout yet.
7. **Fairness and trust.** Flag rate and false-positive rate by group (target: no group's false-positive rate above 1.5 times the lowest), and the share of flags staff dismiss with a reason. Partly demonstrated: the audit on the held-out term shows gaps up to about 2 times (deprivation band, age band), which we report openly and which need review before real use.

---

## 6. Who is the ideal user of your solution?

**Primary users.** Student-support and counselling teams, and the deans or heads of department who own retention. They have limited time and need a short, ranked list of students who need help this week, with reasons.

**Secondary users.** Faculty and mentors, who see flagged students in their own classes and can act early. Students, who see their own courses and can check in or ask for support. Student-success and quality-assurance leads, who need the audit trail and outcome data.

**Institution.** A college or university with a learning platform and regular graded work, from about 1,000 to 20,000 students, where staff cannot track every student by hand. Blended or online programmes are the best fit because online activity is a strong signal. First-year and large-cohort courses are where early warning matters most.

**Why them.** They already have the data (marks, submissions, platform activity) and they already carry the duty of care. What they lack is time-ordered, explainable warnings and a workflow that closes the loop.

---

## 7. Show the proof that the problem exists.

**A. Students leave in large numbers (external, sources opened).**

- United States, NCES Digest Table 326.30: of first-time, full-time degree-seeking undergraduates who started in fall 2020, 75.7% were retained at the same institution in fall 2021, so about 24% were not. At 4-year institutions the figure was 80.6%. For part-time students it was 43.4%. https://nces.ed.gov/programs/digest/d22/tables/dt22_326.30.asp
- UNESCO Global Education Monitoring report, 25 March 2026, as reported by Times Higher Education: global tertiary gross enrolment ratio rose from 19% (2000) to 44% (2024), while the first-degree gross graduation ratio rose from 17% to 27%. Bachelor's first-year dropout is 15% or more in Australia, Denmark, Iceland, Slovenia and Poland, and above 20% in Brazil, Colombia and Peru. https://www.timeshighereducation.com/news/dropouts-rise-globally-university-participation-surges
- United Kingdom, HESA UK Performance Indicators (2019/20 entrants, published 17 March 2022, as reproduced in a UK government statement): 5.3% of young full-time first-degree entrants did not continue into year two, 11.9% for mature entrants, and a projected 9.4% of full-time first-degree entrants leave with no award. The UK figure is the lowest in the series, which shows that some systems do keep attrition low. https://fenews.co.uk/?p=142876

**B. Existing practice is late, and early predictions are a trade-off (sources opened).**

- Howard, Meehan and Parnell (2018, *The Internet and Higher Education* 37:66-75) found weeks 5 to 6, roughly halfway through a semester, to be the best time to run an early-warning system. At that point a Bayesian tree model predicted final marks with a mean absolute error of 6.5 percentage points. Earlier means less accuracy, later means less time to help. https://mural.maynoothuniversity.ie/13275

**C. The problem is measurable in open data (verified in this repo).**

The Open University Learning Analytics Dataset (OULAD) is open data (CC BY 4.0) with 32,593 student enrolments in 22 course runs, 173,912 assessment results and 10,655,280 click-summary rows (Kuzilek, Hlosta, Zdrahal, *Scientific Data* 4:170171, 2017; https://pmc.ncbi.nlm.nih.gov/articles/PMC5704676/). We counted the outcomes in `ml/data/raw/oulad/studentInfo.csv` ourselves:

- 52.8% of enrolments ended in withdrawal (10,156, 31.2%) or failure (7,052, 21.6%). Only 47.2% passed.
- Of the 10,072 withdrawals with a recorded date, 46.6% happened before the first non-exam assessment of that course run was due. A system that waits for marks cannot see these students. The median recorded withdrawal day is day 27 of the term.

**D. Why a simple rule is not enough (our own measurement).**

On the held-out term, a rules-only score reaches ROC-AUC 0.689. The DISHA model reaches 0.857 and warned a median of 54 days before withdrawal. Source: `ml/artifacts_rolling/report.md`.

---

## Verification notes for the team

**Source URLs opened for section 7, and the exact figure used**

| URL | Figure used |
|---|---|
| https://nces.ed.gov/programs/digest/d22/tables/dt22_326.30.asp | Fall 2020 to fall 2021 retention: all institutions full-time 75.7%, part-time 43.4%; 4-year full-time 80.6%. "About 24% not retained" is 100 minus 75.7 (our arithmetic). Retention here means the same institution, not any institution. |
| https://www.timeshighereducation.com/news/dropouts-rise-globally-university-participation-surges | UNESCO GEM report, 25 March 2026: gross enrolment 19% to 44% (2000 to 2024); first-degree graduation ratio 17% to 27%; first-year dropout thresholds (15%+, 20%+). We read the Times Higher Education report, not the UNESCO PDF. |
| https://fenews.co.uk/?p=142876 | 5.3% (young), 11.9% (mature), projected 9.4% no award; 2019/20 entrants; HESA UKPI published 17 March 2022. This is a secondary page quoting a government statement. The HESA page itself returned 403. |
| https://mural.maynoothuniversity.ie/13275 | Howard, Meehan, Parnell 2018: weeks 5 to 6 best; mean absolute error 6.5 percentage points by week 6. |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC5704676/ | 32,593 students, 22 module-presentations, 173,912 assessment rows, 10,655,280 click rows. The paper does not state the withdraw/fail share. |
| `ml/data/raw/oulad/*.csv` (our own count) | studentInfo: 32,593 rows; Pass 12,361, Distinction 3,024, Withdrawn 10,156, Fail 7,052. studentRegistration: 10,072 dated unregistrations, median day 27, 46.6% before the first non-exam assessment due date (computed with assessments.csv, 22 course runs, median first due day 21.5). |

**Could not verify, so left out**
- India AISHE: the official AISHE 2021-22 PDF (education.gov.in) returned 403. Search snippets gave a gross enrolment ratio of 28.4% and about 4.33 crore enrolment, and no higher-education dropout figure. None of it is in the answers. If you want an India figure, open the AISHE PDF yourself and cite the exact page.
- National Student Clearinghouse persistence (76.5%) and retention (68.2%): the blog page did not name the cohort year clearly, and the 2022 PDF could not be read as text. Left out. NCES is used instead.
- Hlosta, Zdrahal, Zendulka (LAK 2017, Ouroboros) and Open University retention claims: only search snippets, the full texts returned 403. Not used.
- OECD Education at a Glance completion figures: not found in the searches. Not used.
- Any external statistic on how noisy or late current early-warning tools are, beyond Howard et al. Search surfaced single studies with different definitions, so they are not comparable and we did not cite them.

**Inaccuracies found in the README or ML_BRIEFING (not fixed)**
- The task brief says "roughly 40% of OULAD enrolments end in withdrawal or failure". The raw file says 52.8% (31.2% withdrawn plus 21.6% failed). The 41.9% in the README is the at-risk base rate of training snapshot rows (17,488 students), a different quantity. We used 52.8%. Please do not say 40%.
- The README says OULAD has 173,913 assessment results. The dataset paper says 173,912. Trivial, but check the file row count before quoting it.
- The README says the model training cut-offs are chosen to hit 85%, 70% and 50% precision. On the unseen term the HIGH tier reached 81.7%, not 85%. The README does report 81.7% beside it, so it is accurate but could be misread. MEDIUM tier on the test term is only 45.6% precise (957 rows), which is below its 70% target. Do not state that all tier targets were met on the test term.
- The README states the stack versions (for example FastAPI 0.162). The API `pyproject.toml` only pins minimums (fastapi >= 0.110, SQLAlchemy >= 2.0.28). We did not check installed versions, and did not quote them.
- The README claims 268 API tests and 76 ML tests. We did not run them and did not use those counts.
- The README says "Counsellors see cases assigned to them or still unassigned". We did not trace this rule in code, so it is not used.
- The "ever flagged" precision of 67.5% is per student. The row-level HIGH+MEDIUM precision is 79.9%. "About 7 in 10 flags correct" refers to the per-student figure. Keep the wording consistent.
- ML_BRIEFING says "about 8 in 10 struggling students were flagged at some point". That matches the report (79.6%), but "flagged" there means HIGH or MEDIUM, not WATCH.
- Verified in code and consistent with the README: 14-state case workflow (`api/app/shared/enums.py`), SHA-256 append-only audit chain with an admin-only verify endpoint, small-cell suppression at 5, HMAC-salted id hashing in Meko, Meko playbook promotion after 3 improvements, decision traces for flag accept and dismiss, Google sign-in exchanged for a DISHA token, demographics excluded from inputs (`manifest.json`).
