"""Convert OULAD into the canonical rolling-model schema (disha_ml.rolling.schema).

Source: Kuzilek J., Hlosta M., Zdrahal Z., "Open University Learning Analytics
dataset", Scientific Data 4, 170171 (2017), CC BY 4.0. See data/raw/oulad/SOURCE.md.

    python -m disha_ml.converters.oulad --raw data/raw/oulad --out data/processed/oulad

Mapping
| Canonical                      | OULAD                                               |
| students.student_id            | id_student                                          |
| students.program_level         | "ug" (all OU modules are degree-level)              |
| students.prior_education_ord   | highest_education -> 0..4 (see EDU_ORD)             |
| students.<audit columns>       | gender, region, imd_band, disability, age_band      |
| enrolments.course_id / term_id | code_module / code_presentation                     |
| enrolments.term_length_days    | courses.module_presentation_length                  |
| enrolments.outcome             | final_result (Pass, Distinction, Fail, Withdrawn)   |
| enrolments.prev_attempts       | num_of_prev_attempts                                |
| enrolments.credit_load         | studied_credits                                     |
| assessments.due_day / weight   | assessments.date (blank exam date -> term length) / weight |
| assessments.type               | TMA, CMA or Exam                                    |
| results.submitted_day/score_pct| studentAssessment.date_submitted / score            |
| activity.count                 | studentVle.sum_click, summed per student per day    |
| withdrawals.day                | studentRegistration.date_unregistration             |

prior_education_ord stands in for 10th/12th/entrance marks, which OULAD does not
have: No Formal quals=0, Lower Than A Level=1, A Level=2, HE Qualification=3,
Postgraduate=4. Not used: `vle` (activity types), `is_banked`, date_registration.
Dates in OULAD are already days relative to the presentation start.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from ..rolling.schema import AUDIT_COLUMNS, save_tables, validate

EDU_ORD = {"No Formal quals": 0, "Lower Than A Level": 1, "A Level or Equivalent": 2,
           "HE Qualification": 3, "Post Graduate Qualification": 4}
CHUNK = 3_000_000


def _daily_activity(path: Path) -> pd.DataFrame:
    """Sum clicks per student per day, reading the ~10M-row file in chunks."""
    parts = []
    cols = ["code_module", "code_presentation", "id_student", "date", "sum_click"]
    dtypes = {"code_module": "category", "code_presentation": "category", "id_student": "int32",
              "date": "int16", "sum_click": "int32"}
    for ch in pd.read_csv(path, usecols=cols, dtype=dtypes, chunksize=CHUNK):
        parts.append(ch.groupby(cols[:4], observed=True, as_index=False)["sum_click"].sum())
    df = pd.concat(parts)
    df = df.groupby(["code_module", "code_presentation", "id_student", "date"], observed=True,
                    as_index=False)["sum_click"].sum()
    return df.rename(columns={"code_module": "course_id", "code_presentation": "term_id",
                              "id_student": "student_id", "date": "day", "sum_click": "count"})


def convert(raw: str | Path) -> Dict[str, pd.DataFrame]:
    raw = Path(raw)
    rd = lambda n: pd.read_csv(raw / f"{n}.csv")  # noqa: E731
    info, courses, asm = rd("studentInfo"), rd("courses"), rd("assessments")
    sa, reg = rd("studentAssessment"), rd("studentRegistration")

    # Student-level baseline and audit fields: from each student's earliest presentation.
    first = info.sort_values("code_presentation").drop_duplicates("id_student")
    students = pd.DataFrame({
        "student_id": first["id_student"], "program_level": "ug", "year_of_study": np.nan,
        "tenth_pct": np.nan, "twelfth_pct": np.nan, "entrance_pct": np.nan,
        "prior_education_ord": first["highest_education"].map(EDU_ORD),
        **{c: first[c] for c in AUDIT_COLUMNS},
    })

    enrol = info.merge(courses, on=["code_module", "code_presentation"], how="left")
    enrolments = pd.DataFrame({
        "student_id": enrol["id_student"], "term_id": enrol["code_presentation"],
        "course_id": enrol["code_module"], "term_start": np.nan,
        "term_length_days": enrol["module_presentation_length"], "outcome": enrol["final_result"],
        "prev_attempts": enrol["num_of_prev_attempts"], "credit_load": enrol["studied_credits"],
    })

    asm = asm.merge(courses, on=["code_module", "code_presentation"], how="left")
    assessments = pd.DataFrame({
        "assessment_id": asm["id_assessment"], "course_id": asm["code_module"],
        "term_id": asm["code_presentation"],
        "due_day": asm["date"].fillna(asm["module_presentation_length"]),  # exams without a date
        "weight": asm["weight"], "type": asm["assessment_type"],
    })
    results = pd.DataFrame({"student_id": sa["id_student"], "assessment_id": sa["id_assessment"],
                            "submitted_day": sa["date_submitted"], "score_pct": sa["score"]})
    gone = reg[reg["date_unregistration"].notna()]
    withdrawals = pd.DataFrame({"student_id": gone["id_student"], "course_id": gone["code_module"],
                                "term_id": gone["code_presentation"], "day": gone["date_unregistration"]})
    activity = _daily_activity(raw / "studentVle.csv")
    return validate({"students": students, "enrolments": enrolments, "assessments": assessments,
                     "results": results, "activity": activity, "withdrawals": withdrawals})


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw", default="data/raw/oulad")
    ap.add_argument("--out", default="data/processed/oulad")
    a = ap.parse_args(argv)
    tables = convert(a.raw)
    save_tables(tables, a.out)
    print({k: len(v) for k, v in tables.items()}, "->", a.out)


if __name__ == "__main__":
    main()
