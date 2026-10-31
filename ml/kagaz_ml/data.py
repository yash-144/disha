"""Load a student dataset and keep only the columns the pipeline uses.

Works out of the box with the UCI 'Predict Students' Dropout and Academic
Success' CSV (semicolon- or comma-separated, header spelling variants).

Your own dataset: describe it in a mapping JSON (see mapping.py and the README):
    {
      "columns":       {"s1_enrolled": "Subjects Registered Sem1", "admission_grade": null, ...},
      "target_values": {"Dropped": "Dropout", "Passed out": "Graduate", "Continuing": "Enrolled"},
      "grade_scale":   10
    }
- "columns" maps a canonical name to your header. null = you don't have it.
- "target_values" maps your outcome values to Dropout / Graduate / Enrolled.
- "grade_scale" is the maximum of your semester grade (10 for SGPA, 100 for
  percentage). Grades are rescaled to 0-20 so rule thresholds keep their meaning.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Canonical name -> accepted header spellings (after normalisation).
COLUMN_ALIASES: Dict[str, List[str]] = {
    "prev_qual_grade": ["previous qualification (grade)"],
    "admission_grade": ["admission grade"],
    "course": ["course"],
    "s1_credited": ["curricular units 1st sem (credited)"],
    "s1_enrolled": ["curricular units 1st sem (enrolled)"],
    "s1_evaluations": ["curricular units 1st sem (evaluations)"],
    "s1_approved": ["curricular units 1st sem (approved)"],
    "s1_grade": ["curricular units 1st sem (grade)"],
    "s1_without_eval": ["curricular units 1st sem (without evaluations)"],
    "s2_credited": ["curricular units 2nd sem (credited)"],
    "s2_enrolled": ["curricular units 2nd sem (enrolled)"],
    "s2_evaluations": ["curricular units 2nd sem (evaluations)"],
    "s2_approved": ["curricular units 2nd sem (approved)"],
    "s2_grade": ["curricular units 2nd sem (grade)"],
    "s2_without_eval": ["curricular units 2nd sem (without evaluations)"],
    # Audit-only columns: used for the fairness check, never as model inputs.
    "gender": ["gender"],
    "age_at_enrollment": ["age at enrollment", "age"],
    "displaced": ["displaced"],
    "special_needs": ["educational special needs"],
    "target": ["target", "output"],
}

MODEL_SOURCE_COLUMNS = [
    "prev_qual_grade", "admission_grade", "course",
    "s1_credited", "s1_enrolled", "s1_evaluations", "s1_approved", "s1_grade", "s1_without_eval",
    "s2_credited", "s2_enrolled", "s2_evaluations", "s2_approved", "s2_grade", "s2_without_eval",
]
AUDIT_COLUMNS = ["gender", "age_at_enrollment", "displaced", "special_needs"]
# Minimum a dataset must have. Everything else may be missing (filled as NaN).
CORE_REQUIRED = ["s1_enrolled", "s1_approved"]

TARGET_VALUES = {"dropout": "Dropout", "graduate": "Graduate", "enrolled": "Enrolled"}
CANONICAL_TARGETS = set(TARGET_VALUES.values())
DEFAULT_GRADE_SCALE = 20.0


def _normalise(header: str) -> str:
    h = str(header).replace("\t", " ").strip().lower()
    return re.sub(r"\s+", " ", h)


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV whose delimiter may be ';' or ','."""
    path = Path(path)
    with path.open("r", encoding="utf-8-sig") as fh:
        first_line = fh.readline()
    sep = ";" if first_line.count(";") > first_line.count(",") else ","
    return pd.read_csv(path, sep=sep, encoding="utf-8-sig")


def load_mapping(path: Optional[str | Path]) -> Optional[Dict]:
    if not path:
        return None
    m = json.loads(Path(path).read_text())
    m.setdefault("columns", {})
    m.setdefault("target_values", {})
    m.setdefault("grade_scale", DEFAULT_GRADE_SCALE)
    unknown = set(m["columns"]) - set(COLUMN_ALIASES)
    if unknown:
        raise ValueError(f"Mapping has unknown canonical names: {sorted(unknown)}; allowed: {sorted(COLUMN_ALIASES)}")
    bad = {k: v for k, v in m["target_values"].items() if v is not None and v not in CANONICAL_TARGETS}
    if bad:
        raise ValueError(f"target_values must map to {sorted(CANONICAL_TARGETS)}; got {bad}")
    return m


def resolve_columns(headers, mapping: Optional[Dict] = None, require_target: bool = True) -> Dict[str, Optional[str]]:
    """canonical name -> header in the file (or None if not available).

    A mapped model column that is absent from the file is an error. A mapped
    audit or target column may be absent (for example a scoring file has no
    outcome), unless the target is required.
    """
    lookup = {_normalise(c): c for c in headers}
    explicit = (mapping or {}).get("columns", {})
    resolved: Dict[str, Optional[str]] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        if canonical in explicit:
            src = explicit[canonical]
            present = src is not None and _normalise(src) in lookup
            strict = canonical in MODEL_SOURCE_COLUMNS or (canonical == "target" and require_target)
            if src is not None and not present and strict:
                raise ValueError(f"Mapping says '{canonical}' is column '{src}', but the file has no such column.")
            resolved[canonical] = lookup[_normalise(src)] if present else None
        else:
            resolved[canonical] = next((lookup[a] for a in aliases if a in lookup), None)
    return resolved


def map_columns(raw: pd.DataFrame, require_target: bool = True, mapping: Optional[Dict] = None) -> pd.DataFrame:
    """Rename known columns to canonical names; fill missing optional ones with NaN."""
    src = resolve_columns(raw.columns, mapping, require_target=require_target)
    missing = [c for c in CORE_REQUIRED if src[c] is None]
    if require_target and src["target"] is None:
        missing.append("target")
    if missing:
        raise ValueError(
            f"Input is missing required columns: {missing}. "
            "For your own dataset, create a mapping file: python -m kagaz_ml.mapping --data <file>"
        )
    out = pd.DataFrame(index=raw.index)
    for c in MODEL_SOURCE_COLUMNS:
        out[c] = raw[src[c]] if src[c] is not None else np.nan
    for c in AUDIT_COLUMNS:
        if src[c] is not None:
            out[c] = raw[src[c]]
    if src["target"] is not None:
        out["target"] = raw[src["target"]]
    return out


def clean(df: pd.DataFrame, mapping: Optional[Dict] = None) -> pd.DataFrame:
    """Type conversion, grade rescaling, target mapping, and the grade-0 quirk.

    A semester grade of 0 (or any grade when no subject was passed) means
    'no average', not a real mark of zero. It becomes NaN; features.py adds a flag.
    """
    df = df.copy()
    mapping = mapping or {}
    for c in [c for c in MODEL_SOURCE_COLUMNS if c != "course"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["course"] = df["course"].astype(str).str.strip().replace({"nan": "unknown", "": "unknown"})

    scale = float(mapping.get("grade_scale", DEFAULT_GRADE_SCALE))
    for s in ("s1", "s2"):
        g = f"{s}_grade"
        if scale != DEFAULT_GRADE_SCALE:
            df[g] = df[g] * (DEFAULT_GRADE_SCALE / scale)
        no_grade = (df[g] <= 0) | (df[f"{s}_approved"] <= 0)
        df.loc[no_grade, g] = np.nan

    if "target" in df.columns:
        values = {str(k).strip(): v for k, v in mapping.get("target_values", {}).items()}
        t = df["target"].astype(str).str.strip()
        df["target"] = t.map(lambda v: values.get(v, v))
        bad = ~df["target"].isin(CANONICAL_TARGETS)
        if bad.any():
            raise ValueError(
                f"Outcome values not understood: {sorted(df.loc[bad, 'target'].astype(str).unique())[:10]}. "
                f"Map each one to {sorted(CANONICAL_TARGETS)} in the mapping file's 'target_values'."
            )
    return df


def load_dataset(path: str | Path, require_target: bool = True, mapping: Optional[Dict] = None) -> pd.DataFrame:
    return clean(map_columns(read_csv(path), require_target=require_target, mapping=mapping), mapping)


def available_checkpoints(df: pd.DataFrame, min_coverage: float = 0.9) -> List[str]:
    """Checkpoints the data supports: semester data must be present for most rows."""
    cps = ["cp0"]
    for cp, s in (("cp1", "s1"), ("cp2", "s2")):
        cover = df[[f"{s}_enrolled", f"{s}_approved"]].notna().all(axis=1).mean()
        if cover >= min_coverage:
            cps.append(cp)
    return cps


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
