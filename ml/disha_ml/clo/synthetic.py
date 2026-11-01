"""Synthetic CO demo data with planted patterns, so every CLO insight shows up.

    python -m disha_ml.clo.synthetic --out /tmp/clo_demo [--seed 7]

One course (CS201, term 2026-odd): 5 COs, sections A and B, ~60 students, assessments IA1 (day 30),
IA2 (day 60) and the end-semester exam (day 110), 14 questions each. Planted patterns:
  CO3  teaching gap: even strong students score low (Q4 is its clearest question)
  CO2  student gap: strong students fine, weak ones not
  Q7   MCQ misconception: 58% pick option B instead of A
  CO4  Bloom: fine on remember/understand, weak on apply/analyse
  CO3  improves in IA2 for section A after a recorded re-teach on day 40
  CO5  declines across the term (a declining-trend example)
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ..rolling.schema import save_tables, validate

COURSE, TERM = "CS201", "2026-odd"
CO_NAMES = {"CO1": "Arrays and complexity", "CO2": "Stacks and queues", "CO3": "Recursion",
            "CO4": "Trees and graphs", "CO5": "Sorting and searching"}
# position in each assessment: (co, bloom level, type)
LAYOUT = [("CO1", 1, "mcq"), ("CO1", 2, "descriptive"), ("CO2", 2, "descriptive"), ("CO3", 3, "descriptive"),
          ("CO3", 2, "descriptive"), ("CO2", 3, "descriptive"), ("CO1", 1, "mcq"), ("CO4", 1, "descriptive"),
          ("CO4", 2, "descriptive"), ("CO4", 3, "descriptive"), ("CO4", 4, "rubric"), ("CO5", 2, "descriptive"),
          ("CO5", 3, "descriptive"), ("CO5", 2, "rubric")]
ASSESSMENTS = [("IA1", 30, "Internal"), ("IA2", 60, "Internal"), ("SEE", 110, "Exam")]


def _frac(co: str, bloom: int, ai: int, section: str, a: float, rng) -> float:
    """Expected share of marks for a student of ability `a` (about N(0,1))."""
    if co == "CO3":     # class-wide gap; section A recovers in IA2 after the re-teach, then fades in SEE
        base = [0.28, 0.66 if section == "A" else 0.28, 0.52 if section == "A" else 0.26][ai]
        f = base + 0.08 * a
    elif co == "CO2":   # only weak students struggle
        f = 0.62 + 0.28 * a
    elif co == "CO4":   # apply/analyse (Bloom >= 3) is weak
        f = (0.80 if bloom <= 2 else 0.30) + 0.10 * a
    elif co == "CO5":   # declining
        f = [0.82, 0.70, 0.58][ai] + 0.10 * a
    else:
        f = 0.78 + 0.10 * a
    return float(np.clip(f + rng.normal(0, 0.08), 0, 1))


def make_tables(n_students: int = 60, seed: int = 7):
    rng = np.random.default_rng(seed)
    ids = [f"S{i + 1:03d}" for i in range(n_students)]
    ability = rng.normal(size=n_students)
    section = ["A" if i % 2 == 0 else "B" for i in range(n_students)]
    qs, qr = [], []
    # Q7: exactly 58% pick B; weaker students are likelier to (rank by -ability plus noise)
    q7_b = set(np.argsort(-ability * 0.8 + rng.normal(0, 1, n_students))[-round(0.58 * n_students):])
    for ai, (aid, _, _) in enumerate(ASSESSMENTS):
        for pos, (co, bloom, typ) in enumerate(LAYOUT):
            qid = f"Q{ai * len(LAYOUT) + pos + 1}"
            mx = 2.0 if typ == "mcq" else 5.0
            correct = "A" if pos == 6 else "C"
            qs.append((qid, aid, co, bloom, mx, typ, correct if typ == "mcq" else None))
            for i, sid in enumerate(ids):
                a, sel, marks = ability[i], None, 0.0
                if typ == "mcq":
                    if qid == "Q7":    # planted misconception
                        sel = "B" if i in q7_b else ("A" if rng.random() < 0.6 else str(rng.choice(["C", "D"])))
                    else:
                        right = rng.random() < np.clip(0.70 + 0.20 * a, 0.05, 0.97)
                        sel = correct if right else str(rng.choice([o for o in "ABCD" if o != correct]))
                    marks = mx if sel == correct else 0.0
                else:
                    marks = round(_frac(co, bloom, ai, section[i], a, rng) * mx * 2) / 2
                qr.append((sid, qid, marks, sel))
    # muddiest-point poll: many name CO3, a few CO4, a free-text topic, and CO5 from too few to show
    fb = [(sid, COURSE, TERM, 45 + int(rng.integers(0, 10)), "CO3", None) for sid in rng.choice(ids, 24, replace=False)]
    fb += [(sid, COURSE, TERM, 50, "CO4", None) for sid in rng.choice(ids, 9, replace=False)]
    fb += [(sid, COURSE, TERM, 52, None, "base cases") for sid in rng.choice(ids, 6, replace=False)]
    fb += [(sid, COURSE, TERM, 55, "CO5", None) for sid in rng.choice(ids, 2, replace=False)]
    t = {
        "students": pd.DataFrame({"student_id": ids, "program_level": "ug", "year_of_study": 2}),
        "enrolments": pd.DataFrame({"student_id": ids, "term_id": TERM, "course_id": COURSE, "term_length_days": 120,
                                    "outcome": "Pass", "section": section}),
        "assessments": pd.DataFrame([(a, COURSE, TERM, d, w, ty) for (a, d, ty), w in zip(ASSESSMENTS, (20, 20, 60))],
                                    columns=["assessment_id", "course_id", "term_id", "due_day", "weight", "type"]),
        "course_outcomes": pd.DataFrame([(COURSE, c, d, 60) for c, d in CO_NAMES.items()],
                                        columns=["course_id", "co_id", "description", "target_pct"]),
        "questions": pd.DataFrame(qs, columns=["question_id", "assessment_id", "co_id", "bloom_level", "max_marks", "type",
                                               "correct_option"]),
        "question_results": pd.DataFrame(qr, columns=["student_id", "question_id", "marks", "selected_option"]),
        "topic_feedback": pd.DataFrame(fb, columns=["student_id", "course_id", "term_id", "day", "co_id", "topic"]),
        "teaching_actions": pd.DataFrame([(COURSE, TERM, "CO3", "A", 40, "re-teach with worked examples")],
                                         columns=["course_id", "term_id", "co_id", "section", "day", "action"]),
    }
    return validate(t)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Write synthetic CO demo tables")
    ap.add_argument("--out", required=True, help="folder to write <table>.csv.gz files into")
    ap.add_argument("--students", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    paths = save_tables(make_tables(a.students, a.seed), a.out)
    print(f"wrote {len(paths)} tables to {a.out}; run: python -m disha_ml.clo.analyze --tables {a.out} "
          f"--course {COURSE} --term {TERM} --no-meko")


if __name__ == "__main__":
    main()
