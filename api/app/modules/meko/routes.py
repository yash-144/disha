import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.core.dependencies import campus_role
from app.core.meko import catalog_entries, get_meko
from app.core.permissions import STAFF_ROLES, Role

try:
    from disha_meko import catalog as cat, guard, playbook as pb
except ImportError:  # Meko is optional
    cat = guard = pb = None

router = APIRouter()
staff = campus_role(*STAFF_ROLES)
# campus knowledge managers: admins plus HoD as the campus coordinator role
manager = campus_role(Role.INSTITUTION_ADMIN, Role.PLATFORM_ADMIN, Role.HOD)
KB_TYPES = {".pdf", ".txt", ".md", ".json", ".csv"}
KB_MAX_BYTES = int(os.getenv("MEKO_KB_MAX_BYTES", str(5 * 1024 * 1024)))


class RecallRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500, examples=["What interventions worked for similar risk profiles?"])
    k: int = Field(default=5, ge=1, le=20)


class RecallResponse(BaseModel):
    answer: str
    sources: List[str] = []


@router.get("/health")
async def meko_health(meko=Depends(get_meko)):
    """Is Meko configured and reachable? Never fails; DISHA works without Meko."""
    tools = await meko.list_tools() if meko.active else []
    return {"configured": meko.active, "reachable": bool(tools), "datapack": meko.cfg.datapack,
            "tool_count": len(tools), "last_error": meko.last_error}


@router.get("/tools")
async def meko_tools(meko=Depends(get_meko), _=Depends(staff)):
    """Discovered Meko tools and the logical operation each is mapped to."""
    return {"tools": await meko.list_tools(), "mapping": await meko.mapping() if meko.active else {}}


@router.post("/recall", response_model=RecallResponse)
async def meko_recall(body: RecallRequest, meko=Depends(get_meko), _=Depends(staff)):
    """Staff ask Meko, e.g. 'what interventions worked for similar risk profiles?'.

    The query is redacted before it leaves DISHA. Do not paste student names.
    """
    answer = await meko.recall(body.query, body.k)
    return RecallResponse(answer=answer or "No prior context available from Meko.")


def _need_meko(meko):
    if not meko.active or guard is None:
        raise HTTPException(503, "Meko is not configured")


@router.post("/knowledge")
async def upload_knowledge(request: Request, file: UploadFile = File(...), doc_type: str = Form("policy"),
                           intervention_id: Optional[str] = Form(None), reason_codes: str = Form(""),
                           meko=Depends(get_meko), _=Depends(manager)):
    """Campus staff upload operational knowledge (policies, procedures). Meko chunks and indexes it.

    Rejected if it contains emails, phone numbers or student IDs. Never used for repo docs.
    """
    _need_meko(meko)
    name = Path(file.filename or "").name
    if Path(name).suffix.lower() not in KB_TYPES:
        raise HTTPException(415, "Only PDF, TXT, MD, JSON or CSV files are accepted")
    data = await file.read(KB_MAX_BYTES + 1)
    if len(data) > KB_MAX_BYTES:
        raise HTTPException(413, f"File exceeds {KB_MAX_BYTES} bytes")
    try:
        guard.check(data)
    except guard.PiiFound as exc:
        raise HTTPException(422, str(exc))
    campus = cat.safe(getattr(request.state, "campus_id", None) or "default")
    codes = sorted(c.strip() for c in reason_codes.split(",") if c.strip())
    if Path(name).suffix.lower() in {".md", ".txt"}:  # linking header; structured formats stay untouched
        head = cat.header(doc_type=doc_type, campus_id=campus, intervention_id=intervention_id, reason_codes=codes)
        data = (head + "\n\n").encode() + data
    res = await meko.upload_bytes(data, f"{campus}__{cat.safe(doc_type)}__{cat.safe(Path(name).stem)}{Path(name).suffix.lower()}")
    if not res or not res["ok"]:
        raise HTTPException(502, f"Meko upload failed: {meko.last_error or 'unknown'}")
    return {"filename": name, "campus_id": campus, "state": res["state"], "key": res["key"]}


@router.get("/knowledge/search")
async def search_knowledge(q: str = Query(min_length=3, max_length=500), limit: int = Query(5, ge=1, le=20),
                           meko=Depends(get_meko), _=Depends(staff)):
    """Chunks Meko indexed from campus knowledge, with the document_id needed to delete a document."""
    hits = await meko.search_knowledge(q, limit) or []
    return {"results": [{"document_id": h.get("document_id"), "chunk_text": h.get("chunk_text"),
                         "distance": h.get("distance")} for h in hits]}


@router.delete("/knowledge/{document_id}")
async def delete_knowledge(document_id: str, meko=Depends(get_meko), _=Depends(manager)):
    _need_meko(meko)
    if not await meko.delete_document(document_id):
        raise HTTPException(502, f"Meko delete failed: {meko.last_error or 'unknown'}")
    return {"document_id": document_id, "deleted": True}


@router.get("/playbook")
async def get_playbook(reason_codes: str = Query(..., min_length=1), tier: Optional[str] = None,
                       meko=Depends(get_meko), _=Depends(staff)):
    """Interventions that improved similar profiles (promoted + recent memories), limited to the campus
    catalogue (AI-07). Advice for a human; nothing is applied."""
    if not meko.active or pb is None:
        return {"suggestions": [], "dropped_not_in_catalogue": 0, "catalogue_size": 0}
    entries = catalog_entries()
    codes = [c.strip().upper() for c in reason_codes.split(",") if c.strip()]
    out = await pb.playbook(meko, codes, tier, cat.active_ids(entries))
    titles = {str(e["id"]): e.get("title") for e in entries}
    for r in out["suggestions"]:
        r["title"] = titles.get(r["intervention_id"])
    if not entries:
        out["note"] = "No campus catalogue configured (MEKO_CATALOG_PATH); nothing can be suggested."
    return out
