import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.core.database import db
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError, StateTransitionError
from app.shared.enums import CaseState, OutcomeStatus
from app.shared.utils import utc_now

class InterventionService:
    @staticmethod
    def get_catalogue(campus_id: str) -> List[dict]:
        with db._lock:
            items = [
                cat for cat in db.intervention_catalog.values()
                if cat.get("active") is True
            ]
            items.sort(key=lambda x: x.get("display_label", ""))
            return items

    @staticmethod
    def select_intervention(
        case_id: str,
        intervention_key: str,
        counsellor_id: str,
        campus_id: str,
        description: Optional[str] = None,
        target_completion_date: Optional[datetime] = None
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can select interventions")

            # Validate intervention catalogue entry
            cat_item = db.intervention_catalog.get(intervention_key)
            if not cat_item or not cat_item.get("active"):
                raise EntityNotFoundError("InterventionCatalogItem", intervention_key)

            # Allowed states: ACCEPTED, SUPPORT_IN_PROGRESS, CONTACT_ATTEMPTED, ACTION_PLANNED
            current_state = case.get("state")
            if current_state not in [
                CaseState.ACCEPTED.value,
                CaseState.CONTACT_ATTEMPTED.value,
                CaseState.SUPPORT_IN_PROGRESS.value,
                CaseState.ACTION_PLANNED.value
            ]:
                raise StateTransitionError(
                    from_state=current_state,
                    to_state=CaseState.SUPPORT_IN_PROGRESS.value,
                    reason=f"Intervention cannot be selected when case is in '{current_state}' state"
                )

            now = utc_now()
            case["selected_intervention_key"] = intervention_key
            
            # Transition to SUPPORT_IN_PROGRESS if currently in ACCEPTED or CONTACT_ATTEMPTED
            target_state = current_state
            if current_state in [CaseState.ACCEPTED.value, CaseState.CONTACT_ATTEMPTED.value]:
                target_state = CaseState.SUPPORT_IN_PROGRESS.value
                case["state"] = target_state

            case["version"] += 1
            case["updated_at"] = now

            db.record_case_event(
                campus_id=campus_id,
                case_id=case_id,
                actor_id=counsellor_id,
                event_type="INTERVENTION_SELECTED",
                from_state=current_state,
                to_state=target_state,
                reason_code=f"SELECTED_{intervention_key}",
                metadata={
                    "intervention_key": intervention_key,
                    "label": cat_item.get("display_label"),
                    "description": description,
                    "target_completion_date": target_completion_date.isoformat() if target_completion_date else None
                }
            )

            outcome = db.case_outcomes.get(case_id)
            return {
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "intervention_key": intervention_key,
                "display_label": cat_item.get("display_label"),
                "domain": cat_item.get("domain"),
                "description": description or cat_item.get("description"),
                "assigned_counsellor_id": counsellor_id,
                "progress": "in_progress",
                "created_at": now,
                "updated_at": now,
                "outcome": outcome
            }

    @staticmethod
    def get_case_intervention(case_id: str, counsellor_id: str, campus_id: str) -> Optional[dict]:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can view this case")

            int_key = case.get("selected_intervention_key")
            if not int_key:
                return None

            cat = db.intervention_catalog.get(int_key, {})
            outcome = db.case_outcomes.get(case_id)

            return {
                "id": f"int-{case_id}",
                "case_id": case_id,
                "intervention_key": int_key,
                "display_label": cat.get("display_label", int_key),
                "domain": cat.get("domain", "counselling"),
                "description": cat.get("description"),
                "assigned_counsellor_id": counsellor_id,
                "progress": "completed" if outcome else "in_progress",
                "created_at": case.get("created_at"),
                "updated_at": case.get("updated_at"),
                "outcome": outcome
            }

    @staticmethod
    def record_outcome(
        case_id: str,
        counsellor_id: str,
        campus_id: str,
        outcome_status: str,
        outcome_notes: str,
        completion_date: Optional[datetime] = None
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can record outcome")

            # Validate outcome status
            valid_statuses = {s.value for s in OutcomeStatus}
            if outcome_status not in valid_statuses:
                raise ValueError(f"Invalid outcome_status '{outcome_status}'. Must be one of: {sorted(list(valid_statuses))}")

            outcome_id = str(uuid.uuid4())
            now = utc_now()
            completed_at = completion_date or now

            outcome_record = {
                "id": outcome_id,
                "case_id": case_id,
                "intervention_key": case.get("selected_intervention_key") or "COUNSELLING_SESSION",
                "counsellor_id": counsellor_id,
                "outcome_status": outcome_status,
                "outcome_notes": outcome_notes,
                "completed_at": completed_at,
                "created_at": now
            }
            db.case_outcomes[case_id] = outcome_record

            # Advance state to OUTCOME_REVIEWED if in SUPPORT_IN_PROGRESS or FOLLOW_UP_DUE
            current_state = case.get("state")
            if current_state in [CaseState.SUPPORT_IN_PROGRESS.value, CaseState.FOLLOW_UP_DUE.value]:
                case["state"] = CaseState.OUTCOME_REVIEWED.value
                case["version"] += 1
                case["updated_at"] = now

                db.record_case_event(
                    campus_id=campus_id,
                    case_id=case_id,
                    actor_id=counsellor_id,
                    event_type="OUTCOME_RECORDED",
                    from_state=current_state,
                    to_state=CaseState.OUTCOME_REVIEWED.value,
                    reason_code=f"OUTCOME_{outcome_status.upper()}",
                    metadata={"outcome_status": outcome_status, "outcome_notes": outcome_notes}
                )
            else:
                db.record_audit_event(
                    actor_id=counsellor_id,
                    campus_id=campus_id,
                    entity_type="case_outcome",
                    entity_id=outcome_id,
                    action="OUTCOME_RECORDED",
                    metadata={"case_id": case_id, "outcome_status": outcome_status}
                )

            return outcome_record
