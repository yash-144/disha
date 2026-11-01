import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.services.case_service import CaseService
from app.services.intervention_service import InterventionService
from app.services.followup_service import FollowUpService
from app.schemas.cases import (
    CaseListItem,
    CaseDetailResponse,
    CaseAcceptRequest,
    CaseStatusUpdateRequest,
    CaseNoteResponse,
    CaseNoteCreateRequest,
    CaseTimelineEventResponse,
    CaseCloseRequest
)
from app.schemas.interventions import (
    InterventionSelectRequest,
    InterventionDetailResponse,
    InterventionOutcomeRecordRequest,
    InterventionOutcomeResponse
)
from app.schemas.followups import (
    FollowUpResponse,
    FollowUpScheduleRequest
)
from app.shared.pagination import PaginatedResponse

router = APIRouter(prefix="/cases", tags=["Case Management"])

require_counsellor = require_roles(Role.COUNSELLOR, Role.INSTITUTION_ADMIN)

# --- MODULE C: CASE MANAGEMENT ---

@router.get("", response_model=PaginatedResponse[CaseListItem])
async def list_cases(
    state: Optional[str] = Query(None, description="Filter by case state"),
    priority: Optional[str] = Query(None, description="Filter by case priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_counsellor)
):
    """C21: View cases assigned to the authenticated counsellor with filtering and pagination."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    items, total = CaseService.list_cases(
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        state=state,
        priority=priority,
        page=page,
        page_size=page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case_detail(
    case_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C22: Full case dossier including student, observations, intervention, follow-ups, and timeline."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.get_case_detail(case_id, counsellor_id, campus_id)

@router.post("/{case_id}/accept", response_model=dict)
async def accept_case(
    case_id: str,
    payload: CaseAcceptRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C23: Atomic case acceptance with optimistic concurrency lock and audit log recording."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.accept_case(
        case_id=case_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        expected_version=payload.expected_version,
        acceptance_notes=payload.acceptance_notes
    )

@router.patch("/{case_id}/status", response_model=dict)
async def update_case_status(
    case_id: str,
    payload: CaseStatusUpdateRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C26: Enforce permitted case lifecycle transitions with ownership verification and audit event generation."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.update_case_status(
        case_id=case_id,
        target_state=payload.target_state,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        expected_version=payload.expected_version,
        reason_code=payload.reason_code,
        notes=payload.notes
    )

@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_case_note(
    case_id: str,
    payload: CaseNoteCreateRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C27: Add general case notes visible within the case dossier."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.add_case_note(
        case_id=case_id,
        author_id=counsellor_id,
        campus_id=campus_id,
        content=payload.content
    )

@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_case_notes(
    case_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C27: Retrieve chronological notes for the specified case."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.list_case_notes(case_id, counsellor_id, campus_id)

@router.get("/{case_id}/timeline", response_model=List[CaseTimelineEventResponse])
async def get_case_timeline(
    case_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C28: Persisted chronological event log tracking assignment, acceptance, status updates and closures."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.get_case_timeline(case_id, counsellor_id, campus_id)

@router.post("/{case_id}/close", response_model=dict)
async def close_case(
    case_id: str,
    payload: CaseCloseRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C32: Close case with validated outcome, closing user record, timestamp, and audit event."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return CaseService.close_case(
        case_id=case_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        expected_version=payload.expected_version,
        reason_code=payload.reason_code,
        closing_notes=payload.closing_notes
    )

# --- MODULE D: INTERVENTIONS ON CASES ---

@router.post("/{case_id}/interventions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def select_intervention(
    case_id: str,
    payload: InterventionSelectRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C34-C35: Select and record an active intervention from catalogue for an accepted case."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return InterventionService.select_intervention(
        case_id=case_id,
        intervention_key=payload.intervention_key,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        description=payload.description,
        target_completion_date=payload.target_completion_date
    )

@router.get("/{case_id}/interventions", response_model=Optional[dict])
async def get_case_intervention(
    case_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C35: Get active intervention details for the case."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return InterventionService.get_case_intervention(case_id, counsellor_id, campus_id)

@router.post("/{case_id}/outcome", response_model=InterventionOutcomeResponse)
async def record_case_outcome(
    case_id: str,
    payload: InterventionOutcomeRecordRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C39: Record intervention outcome (helped, not_helped, mixed, unknown) with completion notes."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return InterventionService.record_outcome(
        case_id=case_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        outcome_status=payload.outcome_status,
        outcome_notes=payload.outcome_notes,
        completion_date=payload.completion_date
    )

# --- MODULE E: FOLLOW-UPS ON CASES ---

@router.post("/{case_id}/followups", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def schedule_followup(
    case_id: str,
    payload: FollowUpScheduleRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C40: Schedule a follow-up action for the assigned case."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return FollowUpService.schedule_followup(
        case_id=case_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        title=payload.title,
        scheduled_at=payload.scheduled_at,
        follow_up_type=payload.follow_up_type,
        notes=payload.notes,
        proof_kind=payload.proof_kind
    )

@router.get("/{case_id}/followups", response_model=List[FollowUpResponse])
async def list_case_followups(
    case_id: str,
    current_user: dict = Depends(require_counsellor)
):
    """C41: List all scheduled and completed follow-ups for this case."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return FollowUpService.list_case_followups(case_id, counsellor_id, campus_id)

