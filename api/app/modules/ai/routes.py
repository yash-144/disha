from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.modules.ai import providers
from app.modules.ai.permissions import CASE_AI_ROLES, EVIDENCE_AI_ROLES, STATUS_ROLES
from app.modules.ai.schemas import AiResult, AiStatusResponse, CaseAiRequest, EvidenceRequest, OutreachRequest
from app.modules.ai.services import AiService, ContextBuilder, require_provider

router = APIRouter(tags=["AI"])


@router.get("/status", response_model=AiStatusResponse)
async def ai_status(tenancy: TenancyContext = Depends(require_role(*STATUS_ROLES))):
    """Whether AI assistance is enabled. Always 200; the other endpoints answer 503 while disabled."""
    return providers.provider_status()


@router.post("/review-brief", response_model=AiResult)
async def review_brief(
    payload: CaseAiRequest,
    tenancy: TenancyContext = Depends(require_role(*CASE_AI_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_provider()
    ctx = await ContextBuilder.for_case(db, tenancy, payload.case_id)
    return await AiService.run(db, tenancy, "review_brief", ctx)


@router.post("/summarize-evidence", response_model=AiResult)
async def summarize_evidence(
    payload: EvidenceRequest,
    tenancy: TenancyContext = Depends(require_role(*EVIDENCE_AI_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_provider()
    ctx = await ContextBuilder.for_student_evidence(db, tenancy, payload.student_id)
    return await AiService.run(db, tenancy, "summarize_evidence", ctx)


@router.post("/suggest-interventions", response_model=AiResult)
async def suggest_interventions(
    payload: CaseAiRequest,
    tenancy: TenancyContext = Depends(require_role(*CASE_AI_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    require_provider()
    ctx = await ContextBuilder.for_case(db, tenancy, payload.case_id)
    ctx = await ContextBuilder.with_catalog(db, ctx)
    return await AiService.run(db, tenancy, "suggest_interventions", ctx)


@router.post("/draft-outreach", response_model=AiResult)
async def draft_outreach(
    payload: OutreachRequest,
    tenancy: TenancyContext = Depends(require_role(*CASE_AI_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    """Draft only: the staff member edits and sends it themselves."""
    require_provider()
    channel = payload.channel if payload.channel in ("email", "sms", "call_script") else "email"
    tone = payload.tone if payload.tone in ("supportive", "formal") else "supportive"
    ctx = await ContextBuilder.for_case(db, tenancy, payload.case_id)
    ctx.blocks = []  # an outreach draft needs no case facts at all
    ctx.facts = []
    return await AiService.run(db, tenancy, "draft_outreach", ctx, params=f"channel={channel}; tone={tone}")
