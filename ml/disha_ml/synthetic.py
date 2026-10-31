"""SYNTHETIC data in the UCI column layout, for tests and smoke runs only.

The numbers are invented. They are never to be shown as real results.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

S = "Curricular units {n} sem ({k})"


def generate(n: int = 1500, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ability = rng.normal(0, 1, n)                      # hidden
    courses = rng.choice([33, 171, 9070, 9119, 9147, 9238, 9500, 9773], n)
    rows = {
        "Previous qualification (grade)": np.clip(130 + 12 * ability + rng.normal(0, 8, n), 95, 190).round(1),
        "Admission grade": np.clip(127 + 12 * ability + rng.normal(0, 8, n), 95, 190).round(1),
        "Course": courses,
        "Gender": rng.integers(0, 2, n),
        "Age at enrollment": rng.choice([18, 19, 20, 22, 25, 30, 40], n),
        "Displaced": rng.integers(0, 2, n),
        "Educational special needs": (rng.random(n) < 0.02).astype(int),
    }
    drift = rng.normal(0, 0.6, n)
    for sem, shift in (("1st", 0.0), ("2nd", drift)):
        eff = ability + shift
        enrolled = rng.choice([5, 6, 6, 7], n)
        pass_p = 1 / (1 + np.exp(-(1.2 + 1.6 * eff)))
        approved = rng.binomial(enrolled, pass_p)
        no_eval = rng.binomial(enrolled - approved, np.clip(0.35 - 0.2 * eff, 0.02, 0.9))
        evaluations = enrolled - no_eval + rng.integers(0, 3, n)
        grade = np.where(approved > 0, np.clip(12.5 + 1.5 * eff + rng.normal(0, 0.8, n), 10, 18.5), 0.0).round(2)
        rows[S.format(n=sem, k="credited")] = (rng.random(n) < 0.05).astype(int)
        rows[S.format(n=sem, k="enrolled")] = enrolled
        rows[S.format(n=sem, k="evaluations")] = evaluations
        rows[S.format(n=sem, k="approved")] = approved
        rows[S.format(n=sem, k="grade")] = grade
        rows[S.format(n=sem, k="without evaluations")] = no_eval
    df = pd.DataFrame(rows)
    risk = -(1.8 * ability + 1.0 * drift) + rng.normal(0, 0.9, n)
    target = np.where(risk > 1.0, "Dropout", np.where(risk > 0.4, "Enrolled", "Graduate"))
    df["Target"] = target
    return df


def write(path: str | Path, n: int = 1500, seed: int = 0, sep: str = ";") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    generate(n, seed).to_csv(path, sep=sep, index=False)
    return path


if __name__ == "__main__":
    print(write("data/synthetic_sample.csv"))
