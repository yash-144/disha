import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from app.core.database import db
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.shared.enums import FollowUpStatus
from app.shared.utils import utc_now

class FollowUpService:
    @staticmethod
    def schedule_followup(
        case_id: str,
        counsellor_id: str,
        campus_id: str,
        title: str,
        scheduled_at: datetime,
        follow_up_type: str = "counselling_session",
        notes: Optional[str] = None,
        proof_kind: Optional[str] = None
    ) -> dict:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: Only the assigned counsellor can schedule follow-ups")

            fu_id = str(uuid.uuid4())
            now = utc_now()
            follow_up = {
                "id": fu_id,
                "institution_id": campus_id,
                "case_id": case_id,
                "title": title,
                "follow_up_type": follow_up_type,
                "contact_status": "scheduled",
                "proof_kind": proof_kind or "counsellor_signoff",
                "scheduled_at": scheduled_at,
                "completed_at": None,
                "completed_by": None,
                "notes": notes,
                "status": FollowUpStatus.SCHEDULED.value,
                "created_at": now
            }
            db.follow_ups[fu_id] = follow_up

            db.record_audit_event(
                actor_id=counsellor_id,
                campus_id=campus_id,
                entity_type="follow_up",
                entity_id=fu_id,
                action="FOLLOWUP_SCHEDULED",
                metadata={"case_id": case_id, "scheduled_at": scheduled_at.isoformat(), "title": title}
            )
            return follow_up

    @staticmethod
    def list_case_followups(case_id: str, counsellor_id: str, campus_id: str) -> List[dict]:
        with db._lock:
            case = db.cases.get(case_id)
            if not case:
                raise EntityNotFoundError("Case", case_id)
            if case.get("institution_id") != campus_id:
                raise PermissionDeniedError("Case does not belong to your campus tenancy")
            if case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: You do not have access to follow-ups for this case")

            items = [
                fu for fu in db.follow_ups.values()
                if fu.get("case_id") == case_id and fu.get("institution_id") == campus_id
            ]
            items.sort(key=lambda x: x.get("scheduled_at", utc_now()))
            return items

    @staticmethod
    def list_counsellor_followups(
        counsellor_id: str,
        campus_id: str,
        upcoming_only: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        with db._lock:
            now = utc_now()
            # Fetch counsellor cases
            my_cases = set(
                cid for cid, c in db.cases.items()
                if c.get("institution_id") == campus_id and c.get("primary_owner_user_id") == counsellor_id
            )

            matched = []
            for fu in db.follow_ups.values():
                if fu.get("institution_id") != campus_id:
                    continue
                if fu.get("case_id") not in my_cases:
                    continue
                if upcoming_only:
                    if fu.get("status") != FollowUpStatus.SCHEDULED.value or fu.get("scheduled_at") < now:
                        continue
                matched.append(fu)

            matched.sort(key=lambda x: x.get("scheduled_at", utc_now()))
            total = len(matched)
            start = (page - 1) * page_size
            end = start + page_size
            return matched[start:end], total

    @staticmethod
    def complete_followup(
        followup_id: str,
        counsellor_id: str,
        campus_id: str,
        completion_notes: Optional[str] = None,
        proof_data: Optional[str] = None
    ) -> dict:
        with db._lock:
            fu = db.follow_ups.get(followup_id)
            if not fu:
                raise EntityNotFoundError("FollowUp", followup_id)
            if fu.get("institution_id") != campus_id:
                raise PermissionDeniedError("Follow-up does not belong to your campus tenancy")

            case = db.cases.get(fu.get("case_id"))
            if not case or case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: You are not assigned to the parent case of this follow-up")

            # Idempotency check: if already completed, return as-is
            if fu.get("status") == FollowUpStatus.COMPLETED.value:
                return fu

            now = utc_now()
            fu["status"] = FollowUpStatus.COMPLETED.value
            fu["contact_status"] = "contact_made"
            fu["completed_at"] = now
            fu["completed_by"] = counsellor_id
            if completion_notes:
                prev_notes = fu.get("notes") or ""
                fu["notes"] = f"{prev_notes}\n[Completed Notes]: {completion_notes}".strip()
            if proof_data:
                fu["proof_data"] = proof_data

            db.record_audit_event(
                actor_id=counsellor_id,
                campus_id=campus_id,
                entity_type="follow_up",
                entity_id=followup_id,
                action="FOLLOWUP_COMPLETED",
                metadata={"case_id": fu.get("case_id"), "completed_at": now.isoformat()}
            )
            return fu

    @staticmethod
    def add_followup_note(
        followup_id: str,
        counsellor_id: str,
        campus_id: str,
        content: str
    ) -> dict:
        with db._lock:
            fu = db.follow_ups.get(followup_id)
            if not fu:
                raise EntityNotFoundError("FollowUp", followup_id)
            if fu.get("institution_id") != campus_id:
                raise PermissionDeniedError("Follow-up does not belong to your campus tenancy")

            case = db.cases.get(fu.get("case_id"))
            if not case or case.get("primary_owner_user_id") != counsellor_id:
                raise PermissionDeniedError("Unauthorized: You are not assigned to the parent case of this follow-up")

            prev_notes = fu.get("notes") or ""
            timestamp = utc_now().strftime("%Y-%m-%d %H:%M UTC")
            fu["notes"] = f"{prev_notes}\n[{timestamp}]: {content}".strip()

            db.record_audit_event(
                actor_id=counsellor_id,
                campus_id=campus_id,
                entity_type="follow_up",
                entity_id=followup_id,
                action="FOLLOWUP_NOTE_ADDED",
                metadata={"case_id": fu.get("case_id")}
            )
            return fu

    @staticmethod
    def get_followup_history(
        counsellor_id: str,
        campus_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        with db._lock:
            my_cases = set(
                cid for cid, c in db.cases.items()
                if c.get("institution_id") == campus_id and c.get("primary_owner_user_id") == counsellor_id
            )

            matched = [
                fu for fu in db.follow_ups.values()
                if fu.get("institution_id") == campus_id and fu.get("case_id") in my_cases
            ]
            matched.sort(key=lambda x: x.get("scheduled_at", utc_now()), reverse=True)
            total = len(matched)
            start = (page - 1) * page_size
            end = start + page_size
            return matched[start:end], total
