from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.modules.documents import chain
from app.modules.documents.permissions import ANCHOR_ROLES, READ_ROLES, UPLOAD_ROLES
from app.modules.documents.schemas import (
    AnchoringStatusResponse,
    DocumentResponse,
    DownloadUrlResponse,
    VerificationResponse,
)
from app.modules.documents.services import DocumentService

router = APIRouter(tags=["Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    kind: str = Form("other"),
    case_id: Optional[str] = Form(None),
    tenancy: TenancyContext = Depends(require_role(*UPLOAD_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file as a draft; SHA-256 is computed while streaming."""
    return await DocumentService.create(db, tenancy, file, kind, case_id)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    case_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenancy: TenancyContext = Depends(require_role(*READ_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.list_documents(db, tenancy, case_id, status_filter, limit, offset)


@router.get("/anchoring/status", response_model=AnchoringStatusResponse)
async def anchoring_status(tenancy: TenancyContext = Depends(require_role(*ANCHOR_ROLES))):
    """Whether on-chain anchoring is configured. Never returns secrets."""
    return chain.feature_status("anchoring")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*READ_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.get_document(db, tenancy, document_id)


@router.post("/{document_id}/versions", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    document_id: str,
    file: UploadFile = File(...),
    tenancy: TenancyContext = Depends(require_role(*UPLOAD_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Editing a finalized document creates a new record; the original is never modified."""
    return await DocumentService.new_version(db, tenancy, document_id, file)


@router.post("/{document_id}/finalize", response_model=DocumentResponse)
async def finalize_document(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*UPLOAD_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.finalize(db, tenancy, document_id)


@router.post("/{document_id}/anchor", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def anchor_document(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*ANCHOR_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Queue anchoring (status anchor_pending); the worker submits and confirms. 503 when the chain is not configured."""
    return await DocumentService.request_anchor(db, tenancy, document_id)


@router.post("/{document_id}/verify", response_model=VerificationResponse)
async def verify_document(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*READ_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    return await DocumentService.verify(db, tenancy, document_id)


@router.get("/{document_id}/download-url", response_model=DownloadUrlResponse)
async def get_download_url(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*READ_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    url, ttl, kind = await DocumentService.download_url(db, tenancy, document_id)
    return DownloadUrlResponse(url=url, expires_in_seconds=ttl, kind=kind)


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    tenancy: TenancyContext = Depends(require_role(*READ_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    doc, data = await DocumentService.download(db, tenancy, document_id)
    return Response(
        content=data,
        media_type=doc.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.document_ref}"',
            "X-Content-SHA256": doc.sha256,
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
