# ML briefing (for presenting to judges)

All numbers below come from the saved model and its test report (`ml/artifacts_rolling/`), measured on a term the model never saw. Nothing here is estimated.

## 1. The model in one minute

It looks at one student in one course, as of today, and answers: **"how likely is this student to fail or drop out of this course?"** It re-answers every week as new marks, submissions and online activity arrive. It gives a percentage, a tier (HIGH, MEDIUM, WATCH, ON TRACK) and the top reasons in plain words. A human always decides what to do next.

- **Type:** gradient-boosted decision trees (a standard, well-trusted method for table data), then calibrated so that "80%" really means about 80 in 100.
- **Trained on:** real data from the Open University (UK): about 32,600 course enrolments over four terms. Trained on three terms, tested on the fourth.
- **Not trained on:** any data from the demo campus. The demo campus is sample data shown to illustrate the product.

## 2. What it looks at (23 inputs in 6 groups) and how much each matters

"Impact" = how much the model's quality drops if that group is scrambled (higher = more important). Measured on the test term.

| Group | What it is, simply | Impact |
|---|---|---|
| Marks level | Average and latest marks, standing in class, gap to class median | **High** (0.084) |
| Online activity | Activity compared with classmates, drop in the last 2 weeks, days since last activity | **High** (0.078) |
| Submissions | How many assessments were submitted, missed, late, missed in a row | **Medium** (0.048) |
| Entry background | Where the student started compared with the class | Small (0.008) |
| Marks trend | Rising or falling marks | Small (0.004) |
| Load and history | Earlier attempts, credit load, year | Small (0.002) |

Marks, online activity and submissions carry almost all of the signal. The rest is a minor tie-breaker.

**Deliberately not used:** gender, region, deprivation, disability, age (kept only to audit fairness), and **physical class attendance** (the model has no attendance input).

## 3. The proof, in plain words

| Claim | Result on the unseen term |
|---|---|
| We warn early | Students who later withdrew were flagged a **median 54 days** before leaving (for half of them, between 25 and 112 days). 70% of them were flagged first. |
| We catch most who struggle | About **8 in 10** students who failed or withdrew had been flagged at some point. |
| Flags are mostly right | About **7 in 10** flagged students really struggled. For the strongest (HIGH) alerts: **8 in 10** (81.7%). |
| Early weeks work too | Ranking quality (ROC-AUC) is 0.73 at 10% of the term, 0.81 at 25%, 0.88 at 50%, 0.93 at 75%. Overall 0.857. |
| Honest probabilities | Calibration error 0.037 (small): predicted risk matches reality. |

Say "alert precision", never "accuracy".

## 4. Likely judge questions

**"You use attendance. Students can get proxy attendance."**
The model has no physical-attendance input, so proxy attendance cannot fool it. What it does read is online activity, which can be faked with scripted clicks. That is why it never relies on activity alone: it also needs submissions and marks. In the real data, students with very high activity but under half of work submitted were at risk 75% of the time (small group, 12 rows).

**"A student is on an internship or has a job, so they are quiet online."**
Quiet online but still submitting on time with good marks (159 cases in the test data): 36% ended at risk, close to the 33% average, and the model rated them 42%. So it does not treat quietness alone as failure. Quiet and missing work is a different story: 99% of those students ended at risk. A counsellor still reviews every case, and can dismiss a flag with a reason.

**"Approved medical leave or exam deferral."**
Not an input today. The case workflow handles it: the counsellor sees the reasons, speaks to the student and can dismiss or close with a note. Adding an "approved leave" marker is the natural next step.

**"A student joined late, or the term just started."**
Early on there is little evidence, so accuracy is lower (0.73 at 10% of the term) and the activity-drop signal needs two weeks of history before it appears. The model handles missing values and gets sharper each week.

**"What about a student who always scores low but is doing fine?"**
Marks are compared with the class and with the student's own trend. A steady low scorer who submits everything is rated lower risk than one whose marks are falling and who is missing work.

**"Is it biased?"**
Demographics are not inputs. We still audit the results by group (`ml/artifacts_rolling/report.md`). The false-alarm rate differs by up to about 2x between some groups (deprivation band, age). "Entry background" is a small input (impact 0.008) and could act partly as a proxy. We say this openly and recommend reviewing it before real deployment.

**"Will it flood staff with alerts?"**
No. Alert levels are capped at 25% of a class, and the campus policy caps how many new cases open per run (45 in the demo).

**"Does it work on our campus? It was trained in the UK."**
Fair challenge. It was trained on one university. The system monitors drift (how different your data looks) on every run and tells you to retrain on your own history. In the demo the drift report does show a large shift, which is expected for sample data.

**"Did you try boosting it with generated data?"**
Yes. We tested mixing in generated student data and measured it on real data. It did not help (ranking quality fell from 0.880 to 0.870 as more was added), so we use real data only.

**"Does this prove the interventions help?"**
No. The model proves it spots trouble early. Whether support improves outcomes is tracked in the product (outcome recorded on every case) and needs a real term to measure. Do not claim impact on students yet.

**"Why not deep learning or an AI chatbot?"**
For table data, boosted trees are as accurate and far easier to explain. Every flag comes with reasons a teacher can check. Probabilities are evidence for a human, not decisions.

## 5. Three things to never say
- "94% accuracy" or any accuracy figure for alerts. Use precision and the plain-language lines above.
- "The demo students are real." The demo campus is sample data; the model's training data is real.
- "It has been proven to improve outcomes." It has been proven to warn early.
