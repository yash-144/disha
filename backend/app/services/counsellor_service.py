import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from app.core.database import db
from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.shared.enums import CaseState, FollowUpStatus
from app.shared.utils import utc_now

class CounsellorService:
    @staticmethod
    def get_dashboard(counsellor_id: str, campus_id: str) -> dict:
        with db._lock:
            now = utc_now()
            
            # Fetch counsellor cases in campus
            my_cases = [
                c for c in db.cases.values()
                if c.get("institution_id") == campus_id and c.get("primary_owner_user_id") == counsellor_id
            ]
            
            # Unique assigned students count
            student_ids = set(c.get("student_id") for c in my_cases)
            assigned_students_count = len(student_ids)
            
            assigned_cases_count = len(my_cases)
            
            # Pending cases (awaiting acceptance)
            pending_cases_count = len([
                c for c in my_cases
                if c.get("state") == CaseState.ASSIGNED.value
            ])
            
            # Active cases
            active_states = {
                CaseState.ACCEPTED.value,
                CaseState.CONTACT_ATTEMPTED.value,
                CaseState.SUPPORT_IN_PROGRESS.value,
                CaseState.FOLLOW_UP_DUE.value
            }
            active_cases_count = len([
                c for c in my_cases
                if c.get("state") in active_states
            ])
            
            # Overdue cases
            overdue_cases_raw = [
                c for c in my_cases
                if c.get("due_at") and c.get("due_at") < now and c.get("state") not in [CaseState.CLOSED.value, CaseState.DISMISSED.value]
            ]
            overdue_cases_count = len(overdue_cases_raw)
            
            overdue_cases_list = []
            for oc in overdue_cases_raw:
                student = db.students.get(oc.get("student_id"), {})
                overdue_cases_list.append({
                    "id": oc.get("id"),
                    "student_id": oc.get("student_id"),
                    "student_name": student.get("display_name"),
                    "priority": oc.get("priority"),
                    "state": oc.get("state"),
                    "due_at": oc.get("due_at"),
                    "selected_intervention_key": oc.get("selected_intervention_key"),
                    "is_escalated": oc.get("is_escalated", False)
                })
            
            # Upcoming follow-ups for this counsellor's cases
            case_id_set = set(c.get("id") for c in my_cases)
            upcoming_followups_raw = [
                fu for fu in db.follow_ups.values()
                if fu.get("institution_id") == campus_id
                and fu.get("case_id") in case_id_set
                and fu.get("status") == FollowUpStatus.SCHEDULED.value
                and fu.get("scheduled_at") >= now
            ]
            upcoming_followups_raw.sort(key=lambda x: x.get("scheduled_at"))
            
            upcoming_followups_list = []
            for fu in upcoming_followups_raw[:10]:
                case = db.cases.get(fu.get("case_id"), {})
                student = db.students.get(case.get("student_id"), {})
                upcoming_followups_list.append({
                    "id": fu.get("id"),
                    "case_id": fu.get("case_id"),
                    "student_id": case.get("student_id"),
                    "student_name": student.get("display_name"),
                    "title": fu.get("title"),
                    "scheduled_at": fu.get("scheduled_at"),
                    "follow_up_type": fu.get("follow_up_type"),
                    "status": fu.get("status")
                })
                
            return {
                "summary": {
                    "assigned_students_count": assigned_students_count,
                    "assigned_cases_count": assigned_cases_count,
                    "pending_cases_count": pending_cases_count,
                    "active_cases_count": active_cases_count,
                    "overdue_cases_count": overdue_cases_count
                },
                "upcoming_followups": upcoming_followups_list,
                "overdue_cases": overdue_cases_list
            }

    @staticmethod
    def get_profile(counsellor_id: str, campus_id: str) -> dict:
        with db._lock:
            profile = db.counselor_profiles.get(counsellor_id)
            if not profile:
                user = db.users.get(counsellor_id)
                if not user:
                    raise EntityNotFoundError("Counsellor", counsellor_id)
                now = utc_now()
                profile = {
                    "id": f"prof-{counsellor_id}",
                    "user_id": counsellor_id,
                    "campus_id": campus_id,
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "phone": None,
                    "designation": "Student Wellbeing Counsellor",
                    "department": "Student Guidance Services",
                    "specializations": ["Academic Support"],
                    "qualification": "Certified Counsellor",
                    "availability_status": "available",
                    "assigned_cohorts": [],
                    "onboarding_status": "VERIFIED",
                    "created_at": now,
                    "updated_at": now
                }
                db.counselor_profiles[counsellor_id] = profile
            return profile

    @staticmethod
    def update_profile(counsellor_id: str, campus_id: str, updates: dict) -> dict:
        with db._lock:
            profile = CounsellorService.get_profile(counsellor_id, campus_id)
            
            # Whitelist of permitted fields (strictly no roles or campus modifications)
            permitted_fields = {"phone", "designation", "department", "specializations", "qualification", "availability_status"}
            applied_changes = {}
            for field in permitted_fields:
                if field in updates and updates[field] is not None:
                    profile[field] = updates[field]
                    applied_changes[field] = updates[field]
                    
            profile["updated_at"] = utc_now()
            
            db.record_audit_event(
                actor_id=counsellor_id,
                campus_id=campus_id,
                entity_type="counsellor_profile",
                entity_id=profile["id"],
                action="PROFILE_UPDATED",
                metadata={"fields_updated": list(applied_changes.keys())}
            )
            return profile

    @staticmethod
    def list_assigned_students(
        counsellor_id: str,
        campus_id: str,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        with db._lock:
            # Find all students assigned to this counsellor
            my_cases = [
                c for c in db.cases.values()
                if c.get("institution_id") == campus_id and c.get("primary_owner_user_id") == counsellor_id
            ]
            my_student_ids = set(c.get("student_id") for c in my_cases)
            
            matched_students = []
            for sid in my_student_ids:
                stu = db.students.get(sid)
                if not stu or stu.get("institution_id") != campus_id:
                    continue
                    
                # Search filter by name or external ref
                if search:
                    s_lower = search.lower()
                    if s_lower not in stu.get("display_name", "").lower() and s_lower not in stu.get("external_ref", "").lower():
                        continue
                        
                active_cases = len([
                    c for c in my_cases
                    if c.get("student_id") == sid and c.get("state") not in [CaseState.CLOSED.value, CaseState.DISMISSED.value]
                ])
                
                matched_students.append({
                    "id": stu.get("id"),
                    "external_ref": stu.get("external_ref"),
                    "display_name": stu.get("display_name"),
                    "department": stu.get("department"),
                    "course": stu.get("course"),
                    "cohort_code": stu.get("cohort_code"),
                    "academic_year": stu.get("academic_year"),
                    "enrollment_status": stu.get("enrollment_status"),
                    "active_case_count": active_cases
                })
                
            matched_students.sort(key=lambda x: x.get("display_name", ""))
            total = len(matched_students)
            
            start = (page - 1) * page_size
            end = start + page_size
            return matched_students[start:end], total

    @staticmethod
    def get_student_detail(student_id: str, counsellor_id: str, campus_id: str) -> dict:
        with db._lock:
            stu = db.students.get(student_id)
            if not stu or stu.get("institution_id") != campus_id:
                raise EntityNotFoundError("Student", student_id)
                
            # Authorize scope: Ensure student has case assigned to this counsellor
            my_cases = [
                c for c in db.cases.values()
                if c.get("student_id") == student_id and c.get("primary_owner_user_id") == counsellor_id and c.get("institution_id") == campus_id
            ]
            if not my_cases:
                raise PermissionDeniedError("Unauthorized: Student is not in your authorized assignment scope")
                
            cases_summary = []
            for c in my_cases:
                cases_summary.append({
                    "case_id": c.get("id"),
                    "priority": c.get("priority"),
                    "state": c.get("state"),
                    "selected_intervention_key": c.get("selected_intervention_key"),
                    "due_at": c.get("due_at"),
                    "created_at": c.get("created_at")
                })
                
            return {
                **stu,
                "assigned_cases": cases_summary
            }

    @staticmethod
    def get_student_observations(student_id: str, counsellor_id: str, campus_id: str) -> List[dict]:
        with db._lock:
            # Verify authorization scope first
            CounsellorService.get_student_detail(student_id, counsellor_id, campus_id)
            
            # Fetch observations for this student (preserving evidence provenance, read-only)
            obs_list = [
                obs for obs in db.observations.values()
                if obs.get("student_id") == student_id and obs.get("institution_id") == campus_id
            ]
            obs_list.sort(key=lambda x: x.get("event_at", utc_now()), reverse=True)
            return obs_list

    @staticmethod
    def get_student_support_history(student_id: str, counsellor_id: str, campus_id: str) -> List[dict]:
        with db._lock:
            # Verify authorization scope first
            CounsellorService.get_student_detail(student_id, counsellor_id, campus_id)
            
            all_cases = [
                c for c in db.cases.values()
                if c.get("student_id") == student_id and c.get("institution_id") == campus_id
            ]
            all_cases.sort(key=lambda x: x.get("created_at", utc_now()), reverse=True)
            
            history = []
            for c in all_cases:
                cid = c.get("id")
                outcome = db.case_outcomes.get(cid)
                fu_count = len([fu for fu in db.follow_ups.values() if fu.get("case_id") == cid])
                
                history.append({
                    "case_id": cid,
                    "priority": c.get("priority"),
                    "state": c.get("state"),
                    "intervention": c.get("selected_intervention_key"),
                    "created_at": c.get("created_at"),
                    "closed_at": c.get("closed_at"),
                    "outcome": outcome,
                    "follow_up_count": fu_count
                })
            return history
