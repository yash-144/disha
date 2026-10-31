"""Ingestion of the canonical rolling-model tables (docs/architecture/INSIGHTS_SPEC.md section 2).

Flow: parse uploaded CSV/XLSX -> `disha_ml.rolling.schema.validate` -> integrity and temporal checks (blueprint 06 §2)
-> link students to the roster -> store rows under an `ImportBatch`. Nothing is generated or defaulted here:
whatever the campus uploads is what the model later sees.
"""
from __future__ import annotations

import hashlib
import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DishaBaseException
from app.modules.audit.services import AuditService
from app.modules.ingestion.models import (
    BATCH_COMMITTED, BATCH_FAILED, BATCH_REJECTED, BATCH_SUPERSEDED, BATCH_VALIDATED,
    ROW_MODELS, TABLE_NAMES, ImportBatch,
)
from app.shared.utils import utc_now

log = logging.getLogger("disha.ingestion")

REQUIRED_TABLES = ("enrolments", "assessments")
CORE_TABLES = TABLE_NAMES
INSERT_CHUNK = 2000
FUTURE_GRACE_DAYS = 1
RANGE_GRACE_DAYS = 30

# stable error codes (blueprint 06 style)
SCHEMA_INVALID = "SCHEMA_INVALID"
MISSING_TABLE = "MISSING_TABLE"
UNREADABLE_FILE = "UNREADABLE_FILE"
UNKNOWN_ASSESSMENT = "UNKNOWN_ASSESSMENT"
UNKNOWN_ENROLMENT = "UNKNOWN_ENROLMENT"
INVALID_TEMPORAL_SEQUENCE = "INVALID_TEMPORAL_SEQUENCE"
INVALID_VALUE = "INVALID_VALUE"
DUPLICATE_KEY = "DUPLICATE_KEY"
PARTIAL_TERM_OVERLAP = "PARTIAL_TERM_OVERLAP"


class IngestionError(DishaBaseException):
    def __init__(self, message: str, status_code: int, code: str, details: Optional[dict] = None):
        super().__init__(message, status_code, {"code": code, **(details or {})})


class UploadedFile:
    def __init__(self, field: str, filename: str, content: bytes):
        self.field, self.filename, self.content = field, filename or field, content
        self.sha256 = hashlib.sha256(content).hexdigest()


def _err(code: str, table: str, message: str, count: int = 1, sample: Optional[Sequence[Any]] = None) -> dict:
    return {"code": code, "table": table, "message": message, "count": int(count),
            "sample": [str(s) for s in list(sample or [])[:5]]}


# ---- parsing ---------------------------------------------------------------------------
def parse_files(files: Sequence[UploadedFile]) -> Tuple[Dict[str, pd.DataFrame], List[dict]]:
    """Files named after a table (`enrolments`, ...) hold that table as CSV; a `workbook` file is an XLSX with one sheet per table."""
    tables: Dict[str, pd.DataFrame] = {}
    errors: List[dict] = []
    for f in files:
        try:
            if f.field == "workbook" or f.filename.lower().endswith((".xlsx", ".xlsm")):
                sheets = pd.read_excel(io.BytesIO(f.content), sheet_name=None, dtype=str)
                for name, df in sheets.items():
                    key = str(name).strip().lower()
                    if key in CORE_TABLES:
                        tables[key] = df
            elif f.field in CORE_TABLES:
                tables[f.field] = pd.read_csv(io.BytesIO(f.content), dtype=str if f.field != "activity" else None,
                                              keep_default_na=True)
            else:
                errors.append(_err(UNREADABLE_FILE, f.field, f"unknown upload field '{f.field}'; use one of {list(CORE_TABLES)} or 'workbook'"))
        except Exception as exc:  # noqa: BLE001 - report any parse failure to the uploader
            errors.append(_err(UNREADABLE_FILE, f.field, f"could not read {f.filename}: {exc}"))
    return tables, errors


# ---- validation ------------------------------------------------------------------------
def _term_starts(enrol: pd.DataFrame) -> Dict[Tuple[str, str], pd.Timestamp]:
    out: Dict[Tuple[str, str], pd.Timestamp] = {}
    if "term_start" not in enrol:
        return out
    for (c, t), g in enrol.groupby(["course_id", "term_id"]):
        d = pd.to_datetime(g["term_start"], errors="coerce").dropna()
        if len(d):
            out[(c, t)] = d.iloc[0]
    return out


def check_integrity(t: Dict[str, pd.DataFrame], now: datetime) -> Tuple[List[dict], List[dict]]:
    """Cross-table and temporal checks on validated tables. Returns (errors, warnings)."""
    errors: List[dict] = []
    warns: List[dict] = []
    enrol, asm, res, act, wd, stu = (t[k] for k in ("enrolments", "assessments", "results", "activity", "withdrawals", "students"))

    if asm["assessment_id"].duplicated().any():
        d = asm.loc[asm["assessment_id"].duplicated(), "assessment_id"]
        errors.append(_err(DUPLICATE_KEY, "assessments", "assessment_id must be unique", len(d), d))
    if len(stu) and stu["student_id"].duplicated().any():
        d = stu.loc[stu["student_id"].duplicated(), "student_id"]
        errors.append(_err(DUPLICATE_KEY, "students", "student_id must be unique", len(d), d))
    if len(res) and res.duplicated(["student_id", "assessment_id"]).any():
        n = int(res.duplicated(["student_id", "assessment_id"]).sum())
        errors.append(_err(DUPLICATE_KEY, "results", "more than one result for the same (student_id, assessment_id)", n))
    for name, df, cols in (("assessments", asm, ["due_day"]), ("results", res, ["submitted_day"]),
                           ("activity", act, ["day", "count"]), ("withdrawals", wd, ["day"])):
        for c in cols:
            bad = int(df[c].isna().sum()) if len(df) else 0
            if bad:
                errors.append(_err(INVALID_VALUE, name, f"{c} is required and must be numeric", bad))
    if len(act) and (act["count"] < 0).any():
        errors.append(_err(INVALID_VALUE, "activity", "count must be >= 0", int((act["count"] < 0).sum())))
    if (enrol["term_length_days"] <= 0).any():
        errors.append(_err(INVALID_VALUE, "enrolments", "term_length_days must be > 0", int((enrol["term_length_days"] <= 0).sum())))

    # referential integrity
    keys = set(zip(enrol["student_id"], enrol["course_id"], enrol["term_id"]))
    if len(res):
        unk = res[~res["assessment_id"].isin(set(asm["assessment_id"]))]
        if len(unk):
            errors.append(_err(UNKNOWN_ASSESSMENT, "results", "result refers to an assessment not in assessments", len(unk), unk["assessment_id"].unique()))
        unk = res[~res["student_id"].isin(set(enrol["student_id"]))]
        if len(unk):
            errors.append(_err(UNKNOWN_ENROLMENT, "results", "result refers to a student with no enrolment", len(unk), unk["student_id"].unique()))
    for name, df in (("activity", act), ("withdrawals", wd)):
        if len(df):
            miss = [k for k in zip(df["student_id"], df["course_id"], df["term_id"]) if k not in keys]
            if miss:
                errors.append(_err(UNKNOWN_ENROLMENT, name, "row refers to a (student_id, course_id, term_id) with no enrolment", len(miss), miss))
    cts = set(zip(enrol["course_id"], enrol["term_id"]))
    miss_a = [k for k in zip(asm["course_id"], asm["term_id"]) if k not in cts]
    if miss_a:
        errors.append(_err(UNKNOWN_ENROLMENT, "assessments", "assessment belongs to a course-term with no enrolments", len(miss_a), miss_a))

    # temporal integrity: nothing may be dated after "now" (needs term_start to turn a day number into a date)
    starts = _term_starts(enrol)
    now_ts = pd.Timestamp(now).tz_localize(None) if pd.Timestamp(now).tzinfo else pd.Timestamp(now)
    limit = now_ts + pd.Timedelta(days=FUTURE_GRACE_DAYS)

    def future(df: pd.DataFrame, day_col: str, course_col: Optional[str], term_col: Optional[str]) -> int:
        if not len(df) or not starts:
            return 0
        n = 0
        for (c, tm), s in starts.items():
            m = (df[course_col] == c) & (df[term_col] == tm) if course_col else None
            sub = df[m] if m is not None else df
            if len(sub):
                n += int((s + pd.to_timedelta(sub[day_col], unit="D") > limit).sum())
        return n

    if len(res) and starts:
        a2 = asm.set_index("assessment_id")[["course_id", "term_id"]]
        r = res.join(a2, on="assessment_id", how="inner")
        n = future(r, "submitted_day", "course_id", "term_id")
        if n:
            errors.append(_err(INVALID_TEMPORAL_SEQUENCE, "results", "result dated in the future relative to the term start and today", n))
    for name, df in (("activity", act), ("withdrawals", wd)):
        n = future(df, "day", "course_id", "term_id")
        if n:
            errors.append(_err(INVALID_TEMPORAL_SEQUENCE, name, "row dated in the future relative to the term start and today", n))

    # soft checks
    tl = enrol.groupby(["course_id", "term_id"])["term_length_days"].max()
    for name, df, col in (("activity", act, "day"), ("withdrawals", wd, "day")):
        if len(df):
            lim = df.join(tl.rename("tl"), on=["course_id", "term_id"])["tl"] + RANGE_GRACE_DAYS
            n = int((df[col] > lim).sum())
            if n:
                warns.append(_err("OUT_OF_TERM_RANGE", name, f"{n} rows are dated well after the term end", n))
    if not len(act):
        warns.append(_err("NO_ACTIVITY", "activity", "no activity table: engagement features will be empty", 0))
    if not len(res):
        warns.append(_err("NO_RESULTS", "results", "no results table: every assessment will count as missed", 0))
    if len(stu):
        n = len(set(enrol["student_id"]) - set(stu["student_id"]))
        if n:
            warns.append(_err("ENROLMENT_WITHOUT_STUDENT_ROW", "students", f"{n} enrolled students have no students row (baseline features will be empty)", n))
    return errors, warns


def validate_upload(files: Sequence[UploadedFile], now: Optional[datetime] = None) -> Tuple[Optional[Dict[str, pd.DataFrame]], List[dict], List[dict]]:
    """Parse + schema-validate + integrity-check. Returns (clean tables or None, errors, warnings)."""
    from disha_ml.rolling.schema import validate  # lazy: the API must still boot without the ml package

    raw, errors = parse_files(files)
    if errors:
        return None, errors, []
    for name in REQUIRED_TABLES:
        if name not in raw:
            errors.append(_err(MISSING_TABLE, name, f"table '{name}' is required"))
    if errors:
        return None, errors, []
    try:
        tables = validate(raw)
    except ValueError as exc:
        return None, [_err(SCHEMA_INVALID, "schema", str(exc))], []
    errors, warns = check_integrity(tables, now or utc_now())
    return (None if errors else tables), errors, warns


# ---- storage ---------------------------------------------------------------------------
def _py(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (np.floating, float)):
        return None if not np.isfinite(v) else float(v)
    if isinstance(v, np.integer):
        return int(v)
    if v is pd.NA or v is pd.NaT:
        return None
    return v


def _records(df: pd.DataFrame, campus_id: str, batch_id: str, model, extra: Optional[Dict[str, Any]] = None) -> List[dict]:
    cols = {c: ("student_ref" if c == "student_id" else c) for c in df.columns}
    attrs = {c.name for c in model.__table__.columns}
    use = {src: dst for src, dst in cols.items() if dst in attrs}
    out = []
    for row in df[list(use)].itertuples(index=False, name=None):
        rec = {dst: _py(v) for dst, v in zip(use.values(), row)}
        rec["campus_id"], rec["batch_id"] = campus_id, batch_id
        if "term_start" in rec and rec["term_start"] is not None:
            rec["term_start"] = str(rec["term_start"])[:32]
        if extra:
            rec.update(extra)
        out.append(rec)
    return out


async def _roster_links(db: AsyncSession, campus_id: str, refs: Sequence[str]) -> Dict[str, str]:
    from app.modules.roster.models import Student
    links: Dict[str, str] = {}
    refs = list(refs)
    for i in range(0, len(refs), 500):
        res = await db.execute(select(Student.student_uid, Student.id).where(
            Student.campus_id == campus_id, Student.student_uid.in_(refs[i:i + 500])))
        links.update({uid: sid for uid, sid in res.all()})
    return links


def digest_of(files: Sequence[UploadedFile]) -> str:
    return hashlib.sha256("\n".join(sorted(f"{f.field}:{f.sha256}" for f in files)).encode()).hexdigest()


async def import_tables(db: AsyncSession, *, campus_id: str, actor_id: str, files: Sequence[UploadedFile],
                        dry_run: bool = False) -> Tuple[ImportBatch, bool]:
    """Validate and (unless dry_run) store an upload. Returns (batch, duplicate). The batch row is always persisted."""
    if not campus_id or campus_id == "platform-global":
        raise IngestionError("Select a campus (X-Campus-ID) before importing data", 400, "CAMPUS_REQUIRED")
    if not files:
        raise IngestionError("No files uploaded", 400, "NO_FILES")
    sha = digest_of(files)

    if not dry_run:
        prev = (await db.execute(select(ImportBatch).where(
            ImportBatch.campus_id == campus_id, ImportBatch.file_sha256 == sha,
            ImportBatch.status == BATCH_COMMITTED).limit(1))).scalar_one_or_none()
        if prev:
            return prev, True

    tables, errors, warns = validate_upload(files)
    batch = ImportBatch(
        id=None, campus_id=campus_id, uploaded_by=actor_id, file_sha256=sha, created_at=utc_now(),
        source_files=[{"table": f.field, "filename": f.filename, "bytes": len(f.content), "sha256": f.sha256} for f in files],
        warnings=warns, validation_errors=errors, row_counts={}, term_ids=[],
        status=BATCH_REJECTED if errors else BATCH_VALIDATED,
    )
    import uuid
    batch.id = str(uuid.uuid4())

    src_files = list(batch.source_files)
    to_supersede: List[ImportBatch] = []
    if tables is not None:
        batch.row_counts = {k: int(len(tables[k])) for k in CORE_TABLES}
        terms = sorted(set(tables["enrolments"]["term_id"]))
        batch.term_ids = terms
        older = (await db.execute(select(ImportBatch).where(
            ImportBatch.campus_id == campus_id, ImportBatch.status == BATCH_COMMITTED))).scalars().all()
        for o in older:
            overlap = set(o.term_ids or []) & set(terms)
            if overlap and not set(o.term_ids or []) <= set(terms):
                errors.append(_err(PARTIAL_TERM_OVERLAP, "enrolments",
                                   f"terms {sorted(overlap)} are already imported in batch {o.id} which also holds other terms; "
                                   "upload a file covering all of that batch's terms", len(overlap), sorted(overlap)))
            elif overlap:
                to_supersede.append(o)
        if errors:
            batch.status, batch.validation_errors, tables = BATCH_REJECTED, errors, None

    if tables is not None and not dry_run:
        enrol_refs = sorted(set(tables["enrolments"]["student_id"]))
        links = await _roster_links(db, campus_id, enrol_refs)
        batch.linked_students = sum(1 for r in enrol_refs if r in links)
        batch.unlinked_students = len(enrol_refs) - batch.linked_students
        batch.status = BATCH_COMMITTED
        batch.committed_at = utc_now()
        db.add(batch)
        await db.flush()
        try:
            for name in CORE_TABLES:
                df = tables[name]
                if not len(df):
                    continue
                model = ROW_MODELS[name]
                recs = _records(df, campus_id, batch.id, model)
                if name in ("students", "enrolments"):
                    for r in recs:
                        r["roster_student_id"] = links.get(r["student_ref"])
                for i in range(0, len(recs), INSERT_CHUNK):
                    await db.execute(model.__table__.insert(), recs[i:i + INSERT_CHUNK])
            for o in to_supersede:
                o.status = BATCH_SUPERSEDED
            await db.flush()
        except Exception:
            await db.rollback()
            log.exception("import %s failed while storing rows", batch.id)
            batch = ImportBatch(
                id=str(uuid.uuid4()), campus_id=campus_id, uploaded_by=actor_id, file_sha256=sha, created_at=utc_now(),
                source_files=src_files, warnings=warns, row_counts={}, term_ids=[], status=BATCH_FAILED,
                validation_errors=[_err("STORAGE_FAILED", "all", "unexpected error while storing rows; nothing was imported")])
            db.add(batch)
            await _audit(db, batch, actor_id)
            await db.commit()
            return batch, False
    else:
        db.add(batch)

    await _audit(db, batch, actor_id, superseded=[o.id for o in to_supersede] if batch.status == BATCH_COMMITTED else [])
    await db.commit()
    return batch, False


async def _audit(db: AsyncSession, batch: ImportBatch, actor_id: str, superseded: Optional[List[str]] = None) -> None:
    await AuditService.record_event(
        db, actor_id=actor_id, campus_id=batch.campus_id, entity_type="import_batch", entity_id=batch.id,
        action=f"ingestion.import.{batch.status}",
        event_metadata={"file_sha256": batch.file_sha256, "row_counts": batch.row_counts, "terms": batch.term_ids,
                        "error_codes": sorted({e["code"] for e in batch.validation_errors or []}),
                        "superseded_batches": superseded or []})


async def list_batches(db: AsyncSession, campus_id: str, page: int, page_size: int) -> Tuple[List[ImportBatch], int]:
    total = (await db.execute(select(func.count()).select_from(ImportBatch).where(ImportBatch.campus_id == campus_id))).scalar_one()
    rows = (await db.execute(select(ImportBatch).where(ImportBatch.campus_id == campus_id)
                             .order_by(ImportBatch.created_at.desc()).limit(page_size).offset((page - 1) * page_size))).scalars().all()
    return list(rows), int(total)


async def get_batch(db: AsyncSession, campus_id: str, batch_id: str) -> Optional[ImportBatch]:
    return (await db.execute(select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.campus_id == campus_id))).scalar_one_or_none()


async def active_batch_ids(db: AsyncSession, campus_id: str) -> List[str]:
    res = await db.execute(select(ImportBatch.id).where(ImportBatch.campus_id == campus_id, ImportBatch.status == BATCH_COMMITTED)
                           .order_by(ImportBatch.committed_at.asc()))
    return [r[0] for r in res.all()]
