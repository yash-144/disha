"""Convert the UPV (Universitat Politecnica de Valencia) dropout dataset into
one row per first-year bachelor's student, in the pipeline's standard columns.

Source: Igualde-Saez A. et al., "StudentDropoutDataset", Zenodo, 2025,
https://doi.org/10.5281/zenodo.17239943, licence CC BY 4.0. Descriptor article:
https://doi.org/10.3390/data10100162.

Usage:
    python -m disha_ml.converters.upv --download --raw-dir data/raw/upv \
        --out data/processed/upv_first_year.csv

What the source contains: one row per student, per course, per academic year
(2018, 2021, 2022), with yearly student-level fields repeated on each row.

What this converter keeps
- Students in their first year of a degree (intake year == academic year),
  enrolled in first-year courses, with an admission grade (bachelor entrants).
- One row per student.

How fields are mapped (all values are known at the checkpoint that uses them)
| Standard column   | UPV source                                   | Note |
| prev_qual_grade   | nota10_hash (entry grade, 0-10)              | |
| admission_grade   | nota14_hash (entry grade, 0-14)              | |
| course            | tit_hash (degree)                            | |
| s1_enrolled       | cred_mat_sem_a / 6                           | credits -> subject equivalents (6 ECTS per subject) |
| s1_approved       | cred_sup_sem_a / 6                           | |
| s2_enrolled       | (cred_mat_sem_b + cred_mat_anu) / 6          | year-long subjects end with semester 2 |
| s2_approved       | (cred_sup_sem_b + cred_sup_anu) / 6          | |
| s2_grade          | mean course grade over the year x 2 (0-20)   | yearly only, so used from cp2; no semester-1 grade |
| s1_attendance     | mean campus Wi-Fi days per month, Sep-Jan    | 2021 and 2022 only |
| s2_attendance     | mean campus Wi-Fi days per month, Feb-Jun    | 2021 and 2022 only |
| displaced         | desplazado_hash                              | fairness check only |
| target            | abandono_hash: A -> Dropout, B -> Retained   | |
| cohort_year       | caca (academic year)                         | for a time-based test |
| student_id        | dni_hash                                     | display only |

Not used: matricula_activa and baja_fecha (they describe what happened after
the year, so they would leak the outcome), parental education and other
background fields (not model inputs by design).
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

ZENODO_RECORD = "https://zenodo.org/records/17239943/files"
YEARS = (2018, 2021, 2022)
CREDITS_PER_SUBJECT = 6.0

STUDENT_FIELDS = [
    "dni_hash", "tit_hash", "anyo_ingreso", "caca", "curso_mas_bajo", "nota10_hash", "nota14_hash",
    "desplazado_hash", "abandono_hash",
    "cred_mat_sem_a", "cred_sup_sem_a", "cred_mat_sem_b", "cred_sup_sem_b", "cred_mat_anu", "cred_sup_anu",
]
SEM1_MONTHS = [(0, 9), (0, 10), (0, 11), (0, 12), (1, 1)]   # (year offset, month)
SEM2_MONTHS = [(1, 2), (1, 3), (1, 4), (1, 5), (1, 6)]


def download(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for y in YEARS:
        target = raw_dir / f"dataset_{y}_hash.zip"
        if target.exists():
            continue
        url = f"{ZENODO_RECORD}/dataset_{y}_hash.zip?download=1"
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, target)


def find_year_file(raw_dir: Path, year: int) -> Path:
    for name in (f"dataset_{year}_hash.csv", f"dataset_{year}_hash.zip"):
        if (raw_dir / name).exists():
            return raw_dir / name
    raise FileNotFoundError(f"No dataset_{year}_hash.csv or .zip in {raw_dir} (use --download).")


def _wifi_cols(year: int, months) -> List[str]:
    return [f"n_wifi_days_{year + dy}_{m}" for dy, m in months]


def convert_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Course-level rows for one academic year -> one row per first-year student."""
    year = int(pd.to_numeric(df["caca"]).iloc[0])
    sem1_cols = [c for c in _wifi_cols(year, SEM1_MONTHS) if c in df.columns]
    sem2_cols = [c for c in _wifi_cols(year, SEM2_MONTHS) if c in df.columns]

    num = ["anyo_ingreso", "caca", "curso_mas_bajo", "nota10_hash", "nota14_hash", "nota_asig_hash",
           "cred_mat_sem_a", "cred_sup_sem_a", "cred_mat_sem_b", "cred_sup_sem_b", "cred_mat_anu", "cred_sup_anu",
           *sem1_cols, *sem2_cols]
    df = df.copy()
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    first_year = (df["anyo_ingreso"] == df["caca"]) & (df["curso_mas_bajo"] == 1) & df["nota10_hash"].notna()
    df = df[first_year]

    keys = ["dni_hash", "tit_hash"]
    students = df.groupby(keys, sort=False).first()
    grade = df.groupby(keys, sort=False)["nota_asig_hash"].mean()

    def credits(a: str, b: str | None = None) -> pd.Series:
        v = students[a].fillna(0)
        if b:
            v = v + students[b].fillna(0)
        return (v / CREDITS_PER_SUBJECT).round(2)

    out = pd.DataFrame(index=students.index)
    out["student_id"] = students.index.get_level_values("dni_hash")
    out["cohort_year"] = year
    out["course"] = students.index.get_level_values("tit_hash")
    out["prev_qual_grade"] = students["nota10_hash"]
    out["admission_grade"] = students["nota14_hash"]
    out["s1_enrolled"] = credits("cred_mat_sem_a")
    out["s1_approved"] = credits("cred_sup_sem_a")
    out["s1_grade"] = np.nan
    out["s1_attendance"] = students[sem1_cols].mean(axis=1, skipna=True).round(2) if sem1_cols else np.nan
    out["s2_enrolled"] = credits("cred_mat_sem_b", "cred_mat_anu")
    out["s2_approved"] = credits("cred_sup_sem_b", "cred_sup_anu")
    out["s2_grade"] = (grade * 2).round(2)
    out["s2_attendance"] = students[sem2_cols].mean(axis=1, skipna=True).round(2) if sem2_cols else np.nan
    out["displaced"] = students["desplazado_hash"]
    out["target"] = students["abandono_hash"].map({"A": "Dropout", "B": "Retained"})
    unknown = out["target"].isna()
    if unknown.any():
        raise ValueError(f"Unexpected abandono_hash values: {students.loc[unknown, 'abandono_hash'].unique()[:5]}")
    return out.reset_index(drop=True)


def read_year(path: Path) -> pd.DataFrame:
    header = pd.read_csv(path, sep=";", nrows=0).columns
    wanted = [c for c in header if c in STUDENT_FIELDS or c == "nota_asig_hash" or c.startswith("n_wifi_days_")]
    return pd.read_csv(path, sep=";", decimal=",", usecols=wanted, low_memory=False)


def convert(raw_dir: Path, years=YEARS) -> pd.DataFrame:
    frames = []
    for y in years:
        conv = convert_frame(read_year(find_year_file(raw_dir, y)))
        print(f"{y}: {len(conv)} first-year students, {int((conv.target == 'Dropout').sum())} dropouts "
              f"({(conv.target == 'Dropout').mean():.1%}), attendance present for "
              f"{conv.s1_attendance.notna().mean():.0%}")
        frames.append(conv)
    return pd.concat(frames, ignore_index=True)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Convert the UPV dropout dataset to standard columns.")
    ap.add_argument("--raw-dir", default="data/raw/upv", help="folder with dataset_<year>_hash.zip or .csv")
    ap.add_argument("--out", default="data/processed/upv_first_year.csv")
    ap.add_argument("--download", action="store_true", help="download the three files from Zenodo first")
    a = ap.parse_args(argv)
    raw_dir = Path(a.raw_dir)
    if a.download:
        download(raw_dir)
    df = convert(raw_dir)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"Wrote {len(df)} students to {a.out}")


if __name__ == "__main__":
    main()
