from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import Role
from app.services.followup_service import FollowUpService
from app.schemas.followups import (
    FollowUpResponse,
    FollowUpCompleteRequest,
    FollowUpNoteRequest
)

router = APIRouter(prefix="/followups", tags=["Follow-up Management"])

require_counsellor = require_roles(Role.COUNSELLOR, Role.INSTITUTION_ADMIN)

@router.patch("/{followup_id}/complete", response_model=FollowUpResponse)
async def complete_followup(
    followup_id: str,
    payload: FollowUpCompleteRequest = FollowUpCompleteRequest(),
    current_user: dict = Depends(require_counsellor)
):
    """C44: Mark scheduled follow-up completed with timestamp and user verification (idempotent)."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return FollowUpService.complete_followup(
        followup_id=followup_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        completion_notes=payload.completion_notes,
        proof_data=payload.proof_data
    )

@router.post("/{followup_id}/notes", response_model=FollowUpResponse)
async def add_followup_note(
    followup_id: str,
    payload: FollowUpNoteRequest,
    current_user: dict = Depends(require_counsellor)
):
    """C45: Append notes to an ongoing or completed follow-up."""
    counsellor_id = current_user.get("sub")
    campus_id = current_user.get("active_campus_id")
    return FollowUpService.add_followup_note(
        followup_id=followup_id,
        counsellor_id=counsellor_id,
        campus_id=campus_id,
        content=payload.content
    )

