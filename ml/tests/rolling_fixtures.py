"""Synthetic canonical tables for the rolling-model tests (no OULAD needed)."""
import numpy as np
import pandas as pd

from disha_ml.rolling.schema import validate


def tiny_tables():
    """One course-term of 4 students, hand-built so every feature can be checked by eye.

    Term of 100 days. Assessments: a1 due day 10, a2 due day 30, ex due day 90 (exam).
    A: 80 on time, then 60 on time.   B: 40 late (day 12), then never submits a2.
    C: 90 and 90.                     D: 70 and 70, but withdraws on day 25.
    """
    enrol = pd.DataFrame({"student_id": list("ABCD"), "term_id": "T", "course_id": "C", "term_length_days": 100,
                          "outcome": ["Pass", "Fail", "Distinction", "Withdrawn"],
                          "prev_attempts": [0, 1, 0, 0], "credit_load": 60})
    students = pd.DataFrame({"student_id": list("ABCD"), "program_level": "ug", "prior_education_ord": [3, 1, 2, 1],
                             "gender": ["F", "M", "F", "M"]})
    asm = pd.DataFrame({"assessment_id": ["a1", "a2", "ex"], "course_id": "C", "term_id": "T",
                        "due_day": [10, 30, 90], "weight": [50, 50, 100], "type": ["TMA", "TMA", "Exam"]})
    res = pd.DataFrame([("A", "a1", 9, 80), ("A", "a2", 29, 60), ("B", "a1", 12, 40), ("C", "a1", 8, 90),
                        ("C", "a2", 28, 90), ("D", "a1", 10, 70), ("D", "a2", 30, 70), ("A", "ex", 90, 55)],
                       columns=["student_id", "assessment_id", "submitted_day", "score_pct"])
    rows = []
    for s in "ACD":
        rows += [(s, "C", "T", d, 2) for d in range(0, 31)]
    rows += [("B", "C", "T", d, 2) for d in range(0, 17)]   # B goes quiet after day 16
    act = pd.DataFrame(rows, columns=["student_id", "course_id", "term_id", "day", "count"])
    wd = pd.DataFrame({"student_id": ["D"], "course_id": "C", "term_id": "T", "day": [25]})
    return validate({"students": students, "enrolments": enrol, "assessments": asm, "results": res,
                     "activity": act, "withdrawals": wd})


def make_tables(n=350, terms=("T1", "T2"), seed=0, length=120):
    """Random cohort per term: ability drives scores, submissions, activity and outcome."""
    rng = np.random.default_rng(seed)
    S, E, A, R, V, W = [], [], [], [], [], []
    sig = lambda x: 1 / (1 + np.exp(-x))  # noqa: E731
    for term in terms:
        due = [20, 50, 80, 115]
        for k, d in enumerate(due):
            A.append((f"{term}a{k}", "C1", term, d, 25, "Exam" if k == 3 else "TMA"))
        for i in range(n):
            sid = f"{term}s{i}"
            ab = rng.normal()
            bad = rng.random() < sig(-1.3 * ab - 0.2)
            wd = int(rng.integers(25, 100)) if bad and rng.random() < 0.5 else None
            outcome = "Withdrawn" if wd is not None else ("Fail" if bad else "Pass")
            S.append((sid, "ug", rng.integers(0, 5), rng.choice(["F", "M"])))
            E.append((sid, term, "C1", length, outcome, 0, 60))
            if wd is not None:
                W.append((sid, "C1", term, wd))
            for k, d in enumerate(due):
                if (wd is not None and d >= wd) or rng.random() > sig(1.8 + ab):
                    continue
                R.append((sid, f"{term}a{k}", d + int(rng.integers(-3, 3)), float(np.clip(68 + 13 * ab + rng.normal(0, 8), 0, 100))))
            for day in range(0, length, 2):
                if wd is None or day < wd:
                    V.append((sid, "C1", term, day, int(rng.poisson(np.exp(1.2 + 0.5 * ab)))))
    return validate({
        "students": pd.DataFrame(S, columns=["student_id", "program_level", "prior_education_ord", "gender"]),
        "enrolments": pd.DataFrame(E, columns=["student_id", "term_id", "course_id", "term_length_days", "outcome",
                                               "prev_attempts", "credit_load"]),
        "assessments": pd.DataFrame(A, columns=["assessment_id", "course_id", "term_id", "due_day", "weight", "type"]),
        "results": pd.DataFrame(R, columns=["student_id", "assessment_id", "submitted_day", "score_pct"]),
        "activity": pd.DataFrame(V, columns=["student_id", "course_id", "term_id", "day", "count"]),
        "withdrawals": pd.DataFrame(W, columns=["student_id", "course_id", "term_id", "day"]),
    })
