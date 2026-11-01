import uuid
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from app.core.database import db
from app.core.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ConcurrencyConflictError,
    StateTransitionError
)
from app.shared.enums import CaseState, CasePriority, FollowUpStatus
from app.shared.utils import utc_now
from app.services.case_state_machine import validate_case_transition

class CaseService:
    @staticmethod
    def list_cases(
        counsellor_id: str,
        campus_id: str,
        state: Optional[str] = None,
        priority: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        with db._lock:
            matched_cases = []
            for c in db.cases.values():
                if c.get("institution_id") != campus_id:
                    continue
                if c.get("primary_owner_user_id") != counsellor_id:
                    continue
                if state and c.get("state") != state:
                    continue
                if priority and c.get("priority") != priority:
                    continue
                
                # Enrich with student information
                student = db.students.get(c.get("student_id"), {})
                enriched = {
                    **c,
                    "student_name": student.get("display_name"),
                    "student_ref": student.get("external_ref"),
                    "department": student.get("department")
                }
                matched_cases.append(enriched)
                
            # Sort by updated_at descending
            matched_cases.sort(key=lambda x: x.get("updated_at", utc_now()), reverse=True)
            total = len(matched_cases)
            
            start = (page - 1) * page_size
            end = start + page_size
            items = matched_cases[start:end]
            return items, total

    @staticmethod
    def get_case_detail(case_id: str, counsellor_id: str, campus_id: str) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("You are not authorized to view this unassigned case")

            student = db.students.get(case.get("student_id"), {})
            owner = db.users.get(case.get("primary_owner_user_id"), {})
            
            # Fetch observations for this student
            observations = [
                obs for obs in db.observations.values()
                if obs.get("student_id") == case.get("student_id") and obs.get("institution_id") == campus_id
            ]
            
            # Fetch follow ups for this case
            follow_ups = [
                fu for fu in db.follow_ups.values()
                if fu.get("case_id") == case_id and fu.get("institution_id") == campus_id
            ]
            follow_ups.sort(key=lambda x: x.get("scheduled_at", utc_now()))
            
            # Fetch notes for this case
            notes = [
                note for note in db.case_notes.values()
                if note.get("case_id") == case_id
            ]
            notes.sort(key=lambda x: x.get("created_at", utc_now()))
            
            # Fetch timeline events
            timeline = [
                event for event in db.case_events
                if event.get("case_id") == case_id
            ]
            timeline.sort(key=lambda x: x.get("created_at", utc_now()))
            
            # Fetch outcome if recorded
            outcome = db.case_outcomes.get(case_id)
            
            # Selected intervention details
            intervention_info = None
            int_key = case.get("selected_intervention_key")
            if int_key and int_key in db.intervention_catalog:
                cat = db.intervention_catalog[int_key]
                intervention_info = {
                    "key": int_key,
                    "label": cat.get("display_label"),
                    "domain": cat.get("domain"),
                    "description": cat.get("description")
                }

            return {
                **case,
                "student": student,
                "primary_owner_name": owner.get("full_name"),
                "selected_intervention": intervention_info,
                "observations": observations,
                "follow_ups": follow_ups,
                "notes": notes,
                "timeline": timeline,
                "outcome": outcome
            }

    @staticmethod
    def accept_case(
        case_id: str,
        counsellor_id: str,
        campus_id: str,
        expected_version: int,
        acceptance_notes: Optional[str] = None
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can accept this case")
            
            # Optimistic concurrency check first
            if case.get("version") != expected_version:
                raise ConcurrencyConflictError(
                    f"Conflict: Expected version {expected_version}, but case has version {case.get('version')}"
                )

            current_state = case.get("state")
            if current_state != CaseState.ASSIGNED.value:
                raise StateTransitionError(
                    from_state=current_state,
                    to_state=CaseState.ACCEPTED.value,
                    reason=f"Case must be in 'assigned' state to accept. Current state: '{current_state}'"
                )
                
            now = utc_now()
            case["state"] = CaseState.ACCEPTED.value
            case["accepted_at"] = now
            case["version"] += 1
            case["updated_at"] = now
            
            # Record Case Event & Immutable Audit Event
            db.record_case_event(
                campus_id=campus_id,
                case_id=case_id,
                actor_id=counsellor_id,
                event_type="CASE_ACCEPTED",
                from_state=current_state,
                to_state=CaseState.ACCEPTED.value,
                reason_code="COUNSELLOR_INTAKE_ACCEPTED",
                metadata={"acceptance_notes": acceptance_notes}
            )
            return case

    @staticmethod
    def update_case_status(
        case_id: str,
        target_state: str,
        counsellor_id: str,
        campus_id: str,
        expected_version: int,
        reason_code: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can update this case")
                
            current_state = case.get("state")
            validate_case_transition(current_state, target_state)
            
            # Optimistic concurrency check
            if case.get("version") != expected_version:
                raise ConcurrencyConflictError(
                    f"Conflict: Expected version {expected_version}, but case has version {case.get('version')}"
                )
                
            now = utc_now()
            case["state"] = target_state
            case["version"] += 1
            case["updated_at"] = now
            
            db.record_case_event(
                campus_id=campus_id,
                case_id=case_id,
                actor_id=counsellor_id,
                event_type="CASE_STATE_CHANGED",
                from_state=current_state,
                to_state=target_state,
                reason_code=reason_code or "STATUS_PROGRESSION",
                metadata={"notes": notes}
            )
            return case

    @staticmethod
    def add_case_note(
        case_id: str,
        author_id: str,
        campus_id: str,
        content: str
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != author_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can add notes to this case")
                
            author = db.users.get(author_id, {})
            note_id = str(uuid.uuid4())
            now = utc_now()
            note = {
                "id": note_id,
                "case_id": case_id,
                "author_user_id": author_id,
                "author_name": author.get("full_name", "Counsellor"),
                "content": content,
                "created_at": now,
                "updated_at": now
            }
            db.case_notes[note_id] = note
            
            db.record_audit_event(
                actor_id=author_id,
                campus_id=campus_id,
                entity_type="case_note",
                entity_id=note_id,
                action="NOTE_ADDED",
                metadata={"case_id": case_id, "note_length": len(content)}
            )
            return note

    @staticmethod
    def list_case_notes(case_id: str, counsellor_id: str, campus_id: str) -> List[dict]:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: You do not have access to notes for this case")
                
            notes = [
                n for n in db.case_notes.values()
                if n.get("case_id") == case_id
            ]
            notes.sort(key=lambda x: x.get("created_at", utc_now()))
            return notes

    @staticmethod
    def get_case_timeline(case_id: str, counsellor_id: str, campus_id: str) -> List[dict]:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: You do not have access to timeline for this case")
                
            events = [
                e for e in db.case_events
                if e.get("case_id") == case_id
            ]
            events.sort(key=lambda x: x.get("created_at", utc_now()))
            return events

    @staticmethod
    def close_case(
        case_id: str,
        counsellor_id: str,
        campus_id: str,
        expected_version: int,
        reason_code: str,
        closing_notes: str
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can close this case")
                
            current_state = case.get("state")
            validate_case_transition(current_state, CaseState.CLOSED.value)
            
            # Check version
            if case.get("version") != expected_version:
                raise ConcurrencyConflictError(
                    f"Conflict: Expected version {expected_version}, but case has version {case.get('version')}"
                )
                
            # Validation rule: Case should have an outcome recorded or valid terminal reason
            outcome = db.case_outcomes.get(case_id)
            if not outcome and current_state not in [CaseState.FAILED_CONTACT.value, CaseState.SERVICE_UNAVAILABLE.value]:
                # If closing directly, create outcome entry from closing notes
                db.case_outcomes[case_id] = {
                    "id": str(uuid.uuid4()),
                    "case_id": case_id,
                    "intervention_key": case.get("selected_intervention_key") or "DIRECT_RESOLVE",
                    "counsellor_id": counsellor_id,
                    "outcome_status": "helped",
                    "outcome_notes": closing_notes,
                    "completed_at": utc_now(),
                    "created_at": utc_now()
                }

            now = utc_now()
            case["state"] = CaseState.CLOSED.value
            case["closed_at"] = now
            case["closed_by"] = counsellor_id
            case["version"] += 1
            case["updated_at"] = now
            
            db.record_case_event(
                campus_id=campus_id,
                case_id=case_id,
                actor_id=counsellor_id,
                event_type="CASE_CLOSED",
                from_state=current_state,
                to_state=CaseState.CLOSED.value,
                reason_code=reason_code,
                metadata={"closing_notes": closing_notes}
            )
            return case
