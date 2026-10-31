from typing import List
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.services.intervention_service import InterventionService
from app.schemas.interventions import (
    InterventionCatalogueItem,
    InterventionOutcomeRecordRequest,
    InterventionOutcomeResponse,
    InterventionDetailResponse
)

router = APIRouter(prefix="/interventions", tags=["Intervention Catalogue & Management"])

require_counsellor = require_roles(Role.COUNSELLOR, Role.INSTITUTION_ADMIN)

@router.get("/catalogue", response_model=List[InterventionCatalogueItem])
async def get_intervention_catalogue(current_user: dict = Depends(require_counsellor)):
    """C33: Retrieve list of currently active institutional intervention types."""
    campus_id = current_user.get("active_campus_id")
    return InterventionService.get_catalogue(campus_id)

@router.post("/{case_id}/outcome", response_model=InterventionOutcomeResponse)
async def record_intervention_outcome(
    case_id: str,
    payload: InterventionOutcomeRecordRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C39: Record completion status and observations for the intervention on this case."""
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
