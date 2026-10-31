"""Canonical-table ingestion endpoints (blueprint 05 §2.3, 06). Campus scoped; admin only."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.modules.ingestion import services
from app.modules.ingestion.models import BATCH_FAILED, BATCH_REJECTED
from app.modules.ingestion.permissions import IMPORT_ROLES
from app.modules.ingestion.schemas import (
    CanonicalSchemaResponse, ImportBatchPage, ImportBatchResponse, TableSpec,
)

router = APIRouter()


def _resp(batch, duplicate: bool = False) -> ImportBatchResponse:
    r = ImportBatchResponse.model_validate(batch)
    r.duplicate = duplicate
    return r


async def _read(upload: Optional[UploadFile], field: str) -> Optional[services.UploadedFile]:
    if upload is None or not upload.filename:
        return None
    data = await upload.read(settings.DISHA_INGEST_MAX_BYTES + 1)
    if len(data) > settings.DISHA_INGEST_MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"{field}: file larger than {settings.DISHA_INGEST_MAX_BYTES} bytes")
    return services.UploadedFile(field, upload.filename, data)


@router.post("/imports", response_model=ImportBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_import(
    dry_run: bool = Query(False, description="validate only; nothing is stored"),
    workbook: Optional[UploadFile] = File(None, description="XLSX with one sheet per canonical table"),
    students: Optional[UploadFile] = File(None),
    enrolments: Optional[UploadFile] = File(None),
    assessments: Optional[UploadFile] = File(None),
    results: Optional[UploadFile] = File(None),
    activity: Optional[UploadFile] = File(None),
    withdrawals: Optional[UploadFile] = File(None),
    ctx: TenancyContext = Depends(require_role(*IMPORT_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Upload the canonical tables (a CSV per table, or one XLSX workbook with a sheet per table).

    201 with the batch on success; 200 with `duplicate: true` for an identical earlier upload;
    422 with the batch and its error list when validation fails (the failed attempt is still recorded).
    """
    named = (("workbook", workbook), ("students", students), ("enrolments", enrolments),
             ("assessments", assessments), ("results", results), ("activity", activity),
             ("withdrawals", withdrawals))
    files = []
    for name, upload in named:
        f = await _read(upload, name)
        if f:
            files.append(f)
    batch, duplicate = await services.import_tables(
        db, campus_id=ctx.campus_id, actor_id=ctx.user_id, files=files, dry_run=dry_run)
    body = _resp(batch, duplicate)
    if batch.status in (BATCH_REJECTED, BATCH_FAILED):
        return JSONResponse(status_code=422, content=body.model_dump(mode="json"))
    if duplicate:
        return JSONResponse(status_code=200, content=body.model_dump(mode="json"))
    return body


@router.get("/imports", response_model=ImportBatchPage)
async def list_imports(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                       ctx: TenancyContext = Depends(require_role(*IMPORT_ROLES)),
                       db: AsyncSession = Depends(get_db)):
    rows, total = await services.list_batches(db, ctx.campus_id, page, page_size)
    return ImportBatchPage(items=[_resp(b) for b in rows], total=total, page=page, page_size=page_size,
                           total_pages=max(1, math.ceil(total / page_size)))


@router.get("/imports/{batch_id}", response_model=ImportBatchResponse)
async def get_import(batch_id: str, ctx: TenancyContext = Depends(require_role(*IMPORT_ROLES)),
                     db: AsyncSession = Depends(get_db)):
    batch = await services.get_batch(db, ctx.campus_id, batch_id)
    if not batch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Import batch not found in the active campus")
    return _resp(batch)


@router.get("/schema", response_model=CanonicalSchemaResponse)
async def canonical_schema(ctx: TenancyContext = Depends(require_role(*IMPORT_ROLES))):
    """The canonical input schema the rolling model consumes (from disha_ml.rolling.schema)."""
    from disha_ml.rolling.schema import CLO_TABLES, TABLES
    specs = [TableSpec(name=n, required=n in services.REQUIRED_TABLES, required_columns=req, optional_columns=opt)
             for n, (req, opt) in TABLES.items() if n not in CLO_TABLES]
    return CanonicalSchemaResponse(
        tables=specs, upload_fields=["workbook", *services.CORE_TABLES],
        notes=["All marks are percentages 0-100; every day is relative to term start (day 0).",
               "Re-uploading a term replaces the earlier batch for that term.",
               "Course-outcome tables are not ingested yet."])
