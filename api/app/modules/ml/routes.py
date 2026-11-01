"""Rolling-model endpoints (blueprint 05 §2.x, INSIGHTS_SPEC.md). Campus scoped, role gated, real data only."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import TenancyContext, require_role
from app.modules.ml import services
from app.modules.ml.permissions import READ_ROLES, RUN_ROLES
from app.modules.ml.schemas import (
    CohortInsightsResponse, DriftResponse, EnrolmentInsight, ModelInfoResponse, RiskScorePage,
    RiskScoreSummary, RunPage, ScoringRunRequest, ScoringRunResponse, StudentInsightResponse,
)

router = APIRouter()


@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info(ctx: TenancyContext = Depends(require_role(*READ_ROLES))):
    """Registry entry for the loaded bundle. 409 MODEL_UNAVAILABLE when no bundle is installed."""
    return services.model_info(await services.get_model())


@router.post("/runs", response_model=ScoringRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_run(body: ScoringRunRequest, ctx: TenancyContext = Depends(require_role(*RUN_ROLES)),
                      db: AsyncSession = Depends(get_db)):
    """Score the campus's ingested data as of a day/date. 409 NO_INGESTED_DATA or MODEL_UNAVAILABLE when inputs are missing."""
    run = await services.run_scoring(db, campus_id=ctx.campus_id, triggered_by=ctx.user_id, req=body)
    out = ScoringRunResponse.model_validate(run)  # before the policy step commits and expires `run`
    out.policy = await services.apply_policy_to_run(db, run, ctx)
    return out


@router.get("/runs", response_model=RunPage)
async def list_runs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db)):
    rows, total = await services.list_runs(db, ctx.campus_id, page, page_size)
    return RunPage(items=[ScoringRunResponse.model_validate(r) for r in rows], total=total, page=page,
                   page_size=page_size, total_pages=max(1, math.ceil(total / page_size)))


@router.get("/runs/{run_id}", response_model=ScoringRunResponse)
async def get_run(run_id: str, ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db)):
    return ScoringRunResponse.model_validate(await services.get_run(db, ctx.campus_id, run_id))


@router.get("/students", response_model=RiskScorePage)
async def list_students(
    tier: Optional[str] = Query(None, pattern="(?i)^(high|medium|watch|on_track)$"),
    course_id: Optional[str] = None, term_id: Optional[str] = None,
    signal_only: bool = Query(False, description="HIGH and MEDIUM only"),
    run_id: Optional[str] = Query(None, description="default: the campus's latest completed run"),
    page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db),
):
    """Scored enrolments of a run, highest risk first. 404 NO_SCORING_RUN until a run has completed."""
    run = await services.get_run(db, ctx.campus_id, run_id) if run_id else await services.latest_run(db, ctx.campus_id, term_id)
    rows, total = await services.list_scores(db, ctx.campus_id, run=run, tier=tier, course_id=course_id, term_id=term_id,
                                             signal_only=signal_only, page=page, page_size=page_size)
    return RiskScorePage(run_id=run.id, as_of_day=run.as_of_day, items=[RiskScoreSummary.model_validate(r) for r in rows],
                         total=total, page=page, page_size=page_size, total_pages=max(1, math.ceil(total / page_size)))


@router.get("/students/{student_key}/insight", response_model=StudentInsightResponse)
async def student_insight(student_key: str, course_id: Optional[str] = None,
                          ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db)):
    """Latest StudentInsight per course-term. `student_key` is the roster student id or `external_student_ref_hash`
    (never the raw campus id, to keep it out of URLs and logs)."""
    rows = await services.student_scores(db, ctx.campus_id, student_key, course_id)
    if not rows:
        raise services.MlError("No score found for this student in the active campus", 404, "STUDENT_NOT_SCORED")
    first = rows[0]
    return StudentInsightResponse(
        student_id=first.student_id, external_student_ref_hash=first.external_student_ref_hash, student_ref=first.student_ref,
        items=[EnrolmentInsight(score=RiskScoreSummary.model_validate(r), insight=r.insight) for r in rows])


@router.get("/cohorts", response_model=CohortInsightsResponse)
async def cohort_insights(course_id: Optional[str] = None, term_id: Optional[str] = None, run_id: Optional[str] = None,
                          ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db)):
    """CohortInsight per course-term from the latest (or given) run (INSIGHTS_SPEC section 6)."""
    run = await services.get_run(db, ctx.campus_id, run_id) if run_id else await services.latest_run(db, ctx.campus_id, term_id)
    cohorts = [c for c in (run.cohorts or []) if (not course_id or c["course_id"] == course_id) and (not term_id or c["term_id"] == term_id)]
    return CohortInsightsResponse(run_id=run.id, as_of_day=run.as_of_day, cohorts=cohorts)


@router.get("/drift", response_model=DriftResponse)
async def drift_report(run_id: Optional[str] = None, ctx: TenancyContext = Depends(require_role(*READ_ROLES)),
                       db: AsyncSession = Depends(get_db)):
    """PSI drift of the scored data against the training reference (INSIGHTS_SPEC section 7)."""
    run = await services.get_run(db, ctx.campus_id, run_id) if run_id else await services.latest_run(db, ctx.campus_id)
    return DriftResponse(run_id=run.id, as_of_day=run.as_of_day, finished_at=run.finished_at, data_drift=run.data_drift or {})


@router.get("/early-warning")
async def early_warning(ctx: TenancyContext = Depends(require_role(*READ_ROLES)), db: AsyncSession = Depends(get_db)):
    """How early students are flagged: first-flag day, share flagged in the first half of term, warning time before
    a student leaves a course, plus the model's held-out benchmark."""
    return await services.early_warning(db, ctx.campus_id)
