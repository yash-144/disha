import hashlib
import logging
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import TenancyContext
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError, StateTransitionError
from app.modules.audit.services import AuditService
from app.modules.cases.models import Case
from app.modules.documents import chain
from app.modules.documents.models import Document, DocumentStatus
from app.modules.documents.permissions import CAMPUS_WIDE_ROLES
from app.modules.documents.schemas import VerificationCheck, VerificationResponse
from app.modules.documents.storage import StorageError, StorageNotConfigured, get_storage
from app.shared.utils import utc_now

logger = logging.getLogger("disha.documents")

DOCUMENT_KINDS = {"case_attachment", "intervention_report", "consent_form", "meeting_minutes", "other"}
_CHUNK = 64 * 1024


def allowed_mime() -> set:
    return {m.strip().lower() for m in settings.DISHA_DOCUMENTS_ALLOWED_MIME.split(",") if m.strip()}


def sniff_matches(content_type: str, data: bytes) -> bool:
    """DOC-02: the bytes must look like the declared type."""
    ct = content_type.lower()
    if ct == "application/pdf":
        return data.startswith(b"%PDF-")
    if ct == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if ct == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if ct in ("text/plain", "text/csv"):
        if b"\x00" in data:
            return False
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True
    return False  # allowlisted but no sniffer: refuse rather than trust the header


def safe_filename(name: Optional[str]) -> str:
    base = (name or "document").replace("\\", "/").split("/")[-1].strip() or "document"
    return "".join(c for c in base if c.isprintable())[:255] or "document"


async def read_upload(upload: UploadFile) -> Tuple[bytes, str]:
    """Stream the upload, hashing while reading and enforcing the size limit (DOC-02, DOC-03)."""
    limit = settings.DISHA_DOCUMENTS_MAX_BYTES
    h = hashlib.sha256()
    buf = bytearray()
    while True:
        chunk = await upload.read(_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > limit:
            raise HTTPException(status_code=413, detail=f"File exceeds the {limit} byte limit")
        h.update(chunk)
    if not buf:
        raise HTTPException(status_code=422, detail="Empty file")
    return bytes(buf), h.hexdigest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class DocumentService:
    # ---- access -------------------------------------------------------------------------------
    @staticmethod
    async def _assigned_case_ids(db: AsyncSession, tenancy: TenancyContext) -> List[str]:
        res = await db.execute(
            select(Case.id).where(Case.campus_id == tenancy.campus_id, Case.assigned_counsellor_id == tenancy.user_id)
        )
        return [r[0] for r in res.all()]

    @staticmethod
    async def _get_in_campus(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> Document:
        res = await db.execute(select(Document).where(Document.id == document_id, Document.campus_id == tenancy.campus_id))
        doc = res.scalar_one_or_none()
        if not doc:  # other campus looks identical to missing
            raise EntityNotFoundError("Document", document_id)
        return doc

    @staticmethod
    async def get_document(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> Document:
        doc = await DocumentService._get_in_campus(db, tenancy, document_id)
        if tenancy.role in CAMPUS_WIDE_ROLES or tenancy.is_platform_admin or doc.uploaded_by == tenancy.user_id:
            return doc
        if doc.case_id and doc.case_id in await DocumentService._assigned_case_ids(db, tenancy):
            return doc
        raise PermissionDeniedError("You do not have access to this document")

    @staticmethod
    async def list_documents(
        db: AsyncSession, tenancy: TenancyContext, case_id: Optional[str], status: Optional[str], limit: int, offset: int
    ) -> List[Document]:
        stmt = select(Document).where(Document.campus_id == tenancy.campus_id)
        if case_id:
            stmt = stmt.where(Document.case_id == case_id)
        if status:
            stmt = stmt.where(Document.status == status)
        if not (tenancy.role in CAMPUS_WIDE_ROLES or tenancy.is_platform_admin):
            assigned = await DocumentService._assigned_case_ids(db, tenancy)
            cond = [Document.uploaded_by == tenancy.user_id]
            if assigned:
                cond.append(Document.case_id.in_(assigned))
            stmt = stmt.where(or_(*cond))
        stmt = stmt.order_by(Document.created_at.desc(), Document.id.desc()).limit(limit).offset(offset)
        return list((await db.execute(stmt)).scalars().all())

    # ---- create -------------------------------------------------------------------------------
    @staticmethod
    async def create(
        db: AsyncSession,
        tenancy: TenancyContext,
        upload: UploadFile,
        kind: str,
        case_id: Optional[str],
        previous: Optional[Document] = None,
    ) -> Document:
        if kind not in DOCUMENT_KINDS:
            raise HTTPException(status_code=422, detail=f"kind must be one of {sorted(DOCUMENT_KINDS)}")
        content_type = (upload.content_type or "").split(";")[0].strip().lower()
        if content_type not in allowed_mime():
            raise HTTPException(status_code=415, detail=f"Content type '{content_type}' is not allowed")
        if case_id:
            case = (await db.execute(select(Case).where(Case.id == case_id, Case.campus_id == tenancy.campus_id))).scalar_one_or_none()
            if not case:
                raise EntityNotFoundError("Case", case_id)
        data, digest = await read_upload(upload)
        if not sniff_matches(content_type, data):
            raise HTTPException(status_code=415, detail="File content does not match its declared type")

        try:
            storage = get_storage()
        except StorageNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        doc_id = str(uuid.uuid4())
        key = f"{tenancy.campus_id}/{doc_id}"
        try:
            await storage.put(key, data)
        except StorageError as exc:
            raise HTTPException(status_code=500, detail=f"Could not store the file: {exc}")

        doc = Document(
            id=doc_id,
            campus_id=tenancy.campus_id,
            document_ref=f"DOC-{doc_id}",
            case_id=case_id,
            kind=kind,
            filename=safe_filename(upload.filename),
            content_type=content_type,
            size_bytes=len(data),
            sha256=digest,
            storage_backend=storage.backend,
            storage_key=key,
            status=DocumentStatus.DRAFT,
            version=(previous.version + 1) if previous else 1,
            previous_version_id=previous.id if previous else None,
            uploaded_by=tenancy.user_id,
        )
        db.add(doc)
        await db.flush()
        await AuditService.record_event(
            db, tenancy.user_id, tenancy.campus_id, "document", doc.id,
            "document.uploaded" if not previous else "document.version_created",
            {"sha256": digest, "size_bytes": len(data), "content_type": content_type, "kind": kind,
             "version": doc.version, "previous_version_id": doc.previous_version_id, "case_id": case_id},
        )
        await db.commit()
        return doc

    @staticmethod
    async def new_version(db: AsyncSession, tenancy: TenancyContext, document_id: str, upload: UploadFile) -> Document:
        prev = await DocumentService.get_document(db, tenancy, document_id)
        if prev.status == DocumentStatus.DRAFT:
            raise StateTransitionError(prev.status, "new_version", "draft documents are replaced by uploading again, not versioned")
        return await DocumentService.create(db, tenancy, upload, prev.kind, prev.case_id, previous=prev)

    # ---- bytes --------------------------------------------------------------------------------
    @staticmethod
    async def _stored_bytes(doc: Document) -> Optional[bytes]:
        try:
            return await get_storage().get(doc.storage_key)
        except (StorageError, StorageNotConfigured):
            return None

    @staticmethod
    async def read_verified_bytes(db: AsyncSession, tenancy: TenancyContext, doc: Document) -> bytes:
        """DOC-03: the stored hash is re-checked against the bytes on every read."""
        data = await DocumentService._stored_bytes(doc)
        if data is None:
            raise HTTPException(status_code=409, detail="Stored bytes are missing")
        if sha256_hex(data) != doc.sha256:
            await DocumentService._mark_mismatch(db, tenancy, doc, "bytes do not match the stored hash on read")
            raise HTTPException(status_code=409, detail="Stored bytes no longer match the recorded SHA-256")
        return data

    @staticmethod
    async def _mark_mismatch(db: AsyncSession, tenancy: TenancyContext, doc: Document, reason: str) -> None:
        if doc.status in (DocumentStatus.FINALIZED, DocumentStatus.ANCHORED, DocumentStatus.ANCHOR_PENDING, DocumentStatus.ANCHOR_FAILED):
            doc.status = DocumentStatus.VERIFICATION_MISMATCH
        doc.last_verified_at = utc_now()
        doc.last_verification_ok = "false"
        await AuditService.record_event(
            db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.verification_mismatch", {"reason": reason}
        )
        await db.commit()

    @staticmethod
    async def download(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> Tuple[Document, bytes]:
        doc = await DocumentService.get_document(db, tenancy, document_id)
        data = await DocumentService.read_verified_bytes(db, tenancy, doc)
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.downloaded", {"sha256": doc.sha256})
        await db.commit()
        return doc, data

    @staticmethod
    async def download_url(db: AsyncSession, tenancy: TenancyContext, document_id: str):
        doc = await DocumentService.get_document(db, tenancy, document_id)
        ttl = settings.DISHA_DOCUMENTS_SIGNED_URL_TTL_SECONDS
        await DocumentService.read_verified_bytes(db, tenancy, doc)
        url = await get_storage().signed_url(doc.storage_key, ttl)
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.download_url_issued", {"signed": bool(url)})
        await db.commit()
        if url:
            return url, ttl, "signed"
        return f"/api/v1/documents/{doc.id}/download", None, "api"

    # ---- lifecycle ----------------------------------------------------------------------------
    @staticmethod
    async def finalize(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> Document:
        doc = await DocumentService.get_document(db, tenancy, document_id)
        if doc.status != DocumentStatus.DRAFT:
            raise StateTransitionError(doc.status, DocumentStatus.FINALIZED, "only drafts can be finalized")
        await DocumentService.read_verified_bytes(db, tenancy, doc)
        doc.status = DocumentStatus.FINALIZED
        doc.finalized_at = utc_now()
        doc.finalized_by = tenancy.user_id
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.finalized", {"sha256": doc.sha256})
        await db.commit()
        return doc

    @staticmethod
    async def request_anchor(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> Document:
        """Queue the document for the worker. Refuses (503) unless the chain is really configured."""
        doc = await DocumentService.get_document(db, tenancy, document_id)
        st = chain.feature_status("anchoring")
        if not st["enabled"]:
            msg = st.get("message") or "Anchoring is not configured"
            logger.warning("Anchor requested for %s but anchoring is disabled: %s", doc.id, msg)
            await AuditService.record_event(
                db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.anchor_unavailable", {"reason": "not_configured"}
            )
            await db.commit()
            raise HTTPException(status_code=503, detail=f"Anchoring is disabled: {msg} The document remains '{doc.status}' and was not anchored.")
        if doc.status not in (DocumentStatus.FINALIZED, DocumentStatus.ANCHOR_FAILED):
            raise StateTransitionError(doc.status, DocumentStatus.ANCHOR_PENDING, "only finalized or anchor_failed documents can be anchored")
        await DocumentService.read_verified_bytes(db, tenancy, doc)
        doc.status = DocumentStatus.ANCHOR_PENDING
        doc.anchor_requested_by = tenancy.user_id
        doc.anchor_requested_at = utc_now()
        doc.anchor_tx_hash = None
        doc.anchor_submitted_at = None
        doc.anchor_error = None
        await AuditService.record_event(db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.anchor_requested", {"sha256": doc.sha256})
        await db.commit()
        return doc

    @staticmethod
    async def verify(db: AsyncSession, tenancy: TenancyContext, document_id: str) -> VerificationResponse:
        """DOC-09: report which checks ran."""
        doc = await DocumentService.get_document(db, tenancy, document_id)
        checks: List[VerificationCheck] = []
        data = await DocumentService._stored_bytes(doc)
        if data is None:
            checks.append(VerificationCheck(name="db_hash_vs_bytes", ran=True, ok=False, detail="stored bytes missing"))
            actual = None
        else:
            actual = sha256_hex(data)
            checks.append(VerificationCheck(
                name="db_hash_vs_bytes", ran=True, ok=actual == doc.sha256,
                detail="recorded SHA-256 matches stored bytes" if actual == doc.sha256 else "recorded SHA-256 differs from stored bytes",
            ))

        client = chain.get_chain_client("anchoring")
        if client is None:
            for name in ("chain_hash_vs_bytes", "chain_record_exists"):
                checks.append(VerificationCheck(name=name, ran=False, detail="chain not configured"))
        elif actual is None:
            for name in ("chain_hash_vs_bytes", "chain_record_exists"):
                checks.append(VerificationCheck(name=name, ran=False, detail="no bytes to hash"))
        else:
            try:
                ts = await client.anchor_timestamp(actual)
                exists = ts > 0
                checks.append(VerificationCheck(
                    name="chain_record_exists", ran=True,
                    ok=exists if doc.status == DocumentStatus.ANCHORED else None,
                    detail="hash of the bytes is on chain" if exists else "no on-chain record for the hash of these bytes",
                ))
                # The registry key is the hash itself, so a record for the bytes' hash proves chain hash == bytes hash.
                checks.append(VerificationCheck(
                    name="chain_hash_vs_bytes", ran=True,
                    ok=exists if doc.status == DocumentStatus.ANCHORED else None,
                    detail="on-chain hash equals SHA-256 of the stored bytes" if exists else "bytes hash has no on-chain match",
                ))
            except Exception as exc:
                logger.warning("Chain verification failed for %s: %s", doc.id, exc)
                for name in ("chain_hash_vs_bytes", "chain_record_exists"):
                    checks.append(VerificationCheck(name=name, ran=False, detail="chain unreachable"))

        ok = all(c.ok is not False for c in checks if c.ran)
        now = utc_now()
        doc.last_verified_at = now
        doc.last_verification_ok = "true" if ok else "false"
        if not ok and doc.status in (DocumentStatus.FINALIZED, DocumentStatus.ANCHORED):
            doc.status = DocumentStatus.VERIFICATION_MISMATCH
        elif ok and doc.status == DocumentStatus.VERIFICATION_MISMATCH:
            doc.status = DocumentStatus.ANCHORED if doc.anchored_at else DocumentStatus.FINALIZED
        await AuditService.record_event(
            db, tenancy.user_id, tenancy.campus_id, "document", doc.id, "document.verified",
            {"ok": ok, "checks": {c.name: (c.ok if c.ran else "not_run") for c in checks}},
        )
        await db.commit()
        return VerificationResponse(document_id=doc.id, document_ref=doc.document_ref, status=doc.status, ok=ok, checks=checks, verified_at=now)
