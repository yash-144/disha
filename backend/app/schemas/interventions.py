from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InterventionCatalogueItem(BaseModel):
    id: str
    institution_id: str
    intervention_key: str
    display_label: str
    domain: str
    description: str
    active: bool

class InterventionSelectRequest(BaseModel):
    intervention_key: str = Field(..., description="Key of the catalogue intervention to select")
    description: Optional[str] = None
    target_completion_date: Optional[datetime] = None

class InterventionDetailResponse(BaseModel):
    id: str
    case_id: str
    intervention_key: str
    display_label: str
    domain: str
    description: Optional[str] = None
    assigned_counsellor_id: str
    progress: str
    created_at: datetime
    updated_at: datetime
    outcome: Optional[Dict[str, Any]] = None

class InterventionOutcomeRecordRequest(BaseModel):
    outcome_status: str = Field(..., description="Outcome: helped, not_helped, mixed, or unknown")
    outcome_notes: str = Field(..., min_length=3, description="Detailed observations and outcome notes")
    completion_date: Optional[datetime] = None

class InterventionOutcomeResponse(BaseModel):
    id: str
    case_id: str
    intervention_key: str
    counsellor_id: str
    outcome_status: str
    outcome_notes: str
    completed_at: datetime
    created_at: datetime

