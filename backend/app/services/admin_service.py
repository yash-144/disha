import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from app.core.database import db
from app.core.security import get_password_hash, verify_password
from app.core.permissions import Role
from app.shared.enums import CaseState, NotificationCategory
from app.shared.utils import utc_now
from app.schemas.admin import (
    AdminDashboardSummary,
    CounsellorWorkloadMetric,
    UserItemResponse,
    UserListResponse,
    InviteStaffRequest,
    InvitationResponse,
    MembershipUpdateRequest,
    CampusDetailResponse,
    CampusUpdateRequest,
    AdminCaseListItem,
    AdminCaseDetail,
    ReassignCaseRequest,
    ImportJobResponse,
    AnalyticsOverviewResponse,
    AuditLogItemResponse,
    AdminProfileResponse,
    AdminProfileUpdateRequest,
    AdminChangePasswordRequest,
)

class AdminService:

    # ----------------------------------------------------
    # A. DASHBOARD
    # ----------------------------------------------------
    @staticmethod
    def get_dashboard_summary(campus_id: str) -> AdminDashboardSummary:
        now = utc_now()
        with db._lock:
            # Students
            campus_students = [s for s in db.students.values() if s.get("institution_id") == campus_id]
            total_students = len(campus_students)

            # Users
            campus_users = [u for u in db.users.values() if u.get("campus_id") == campus_id]
            total_faculty = sum(1 for u in campus_users if Role.FACULTY.value in u.get("roles", []))
            total_counsellors = sum(1 for u in campus_users if Role.COUNSELLOR.value in u.get("roles", []))

            # Cases
            campus_cases = [c for c in db.cases.values() if c.get("institution_id") == campus_id]
            total_active_cases = 0
            pending_cases = 0
            overdue_cases = 0
            resolved_cases = 0

            terminal_states = {CaseState.CLOSED.value, CaseState.DISMISSED.value}
            pending_states = {CaseState.SUGGESTED.value, CaseState.UNDER_REVIEW.value, CaseState.ACTION_PLANNED.value, CaseState.ASSIGNED.value}

            for c in campus_cases:
                state = c.get("state")
                due_at = c.get("due_at")
                if state in terminal_states:
                    resolved_cases += 1
                else:
                    total_active_cases += 1
                    if state in pending_states:
                        pending_cases += 1
                    if due_at and due_at < now:
                        overdue_cases += 1

            # Counsellor workload breakdown
            counsellors = [u for u in campus_users if Role.COUNSELLOR.value in u.get("roles", [])]
            workload: List[CounsellorWorkloadMetric] = []
            for cr in counsellors:
                cid = cr.get("id")
                profile = db.counselor_profiles.get(cid, {})
                c_cases = [c for c in campus_cases if c.get("primary_owner_user_id") == cid]
                c_active = sum(1 for c in c_cases if c.get("state") not in terminal_states)
                c_overdue = sum(1 for c in c_cases if c.get("state") not in terminal_states and c.get("due_at") and c.get("due_at") < now)
                c_resolved = sum(1 for c in c_cases if c.get("state") in terminal_states)

                workload.append(
                    CounsellorWorkloadMetric(
                        user_id=cid,
                        full_name=cr.get("full_name"),
                        email=cr.get("email"),
                        department=profile.get("department") or cr.get("department", "Guidance"),
                        active_cases=c_active,
                        overdue_cases=c_overdue,
                        resolved_cases=c_resolved,
                        availability_status=profile.get("availability_status", "available")
                    )
                )

            # Recent Institutional Activities (Audit log top 10)
            recent_activities = [
                event for event in reversed(db.audit_log)
                if event.get("campus_id") == campus_id
            ][:10]

            # Administrative notifications
            notifications = [
                n for n in reversed(list(db.notifications.values()))
                if n.get("campus_id") == campus_id or n.get("reference_type") in ("campus", "admin")
            ][:10]

            return AdminDashboardSummary(
                total_students=total_students,
                total_faculty=total_faculty,
                total_counsellors=total_counsellors,
                total_active_cases=total_active_cases,
                pending_cases=pending_cases,
                overdue_cases=overdue_cases,
                resolved_cases=resolved_cases,
                counsellor_workload=workload,
                recent_activities=recent_activities,
                administrative_notifications=notifications
            )

    # ----------------------------------------------------
    # B. USERS AND MEMBERSHIPS
    # ----------------------------------------------------
    @staticmethod
    def list_users(
        campus_id: str,
        role: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> UserListResponse:
        with db._lock:
            all_users = [u for u in db.users.values() if u.get("campus_id") == campus_id]

            filtered = []
            for u in all_users:
                if role and role not in u.get("roles", []):
                    continue
                if department and u.get("department", "").lower() != department.lower():
                    continue
                if is_active is not None and u.get("is_active", True) != is_active:
                    continue
                if search:
                    s_lower = search.lower()
                    if s_lower not in u.get("full_name", "").lower() and s_lower not in u.get("email", "").lower():
                        continue
                filtered.append(
                    UserItemResponse(
                        id=u.get("id"),
                        email=u.get("email"),
                        full_name=u.get("full_name"),
                        roles=u.get("roles", []),
                        campus_id=u.get("campus_id"),
                        department=u.get("department"),
                        is_active=u.get("is_active", True),
                        created_at=u.get("created_at"),
                        updated_at=u.get("updated_at")
                    )
                )

            total = len(filtered)
            start = (page - 1) * limit
            items = filtered[start:start + limit]

            return UserListResponse(
                items=items,
                total=total,
                page=page,
                limit=limit
            )

    @staticmethod
    def get_user_details(campus_id: str, user_id: str) -> UserItemResponse:
        with db._lock:
            u = db.users.get(user_id)
            if not u or u.get("campus_id") != campus_id:
                raise HTTPException(status_code=404, detail="User not found in this campus")
            return UserItemResponse(
                id=u.get("id"),
                email=u.get("email"),
                full_name=u.get("full_name"),
                roles=u.get("roles", []),
                campus_id=u.get("campus_id"),
                department=u.get("department"),
                is_active=u.get("is_active", True),
                created_at=u.get("created_at"),
                updated_at=u.get("updated_at")
            )

    @staticmethod
    def invite_staff(campus_id: str, admin_user_id: str, payload: InviteStaffRequest) -> InvitationResponse:
        now = utc_now()
        with db._lock:
            # Check if user already exists
            for u in db.users.values():
                if u.get("email").lower() == payload.email.lower() and u.get("campus_id") == campus_id:
                    raise HTTPException(status_code=400, detail="User already registered in this campus")

            # Check if pending invitation exists
            for inv in db.invitations.values():
                if inv.get("email").lower() == payload.email.lower() and inv.get("campus_id") == campus_id and inv.get("status") == "PENDING":
                    raise HTTPException(status_code=400, detail="Active pending invitation already exists for this email")

            inv_id = f"inv-{uuid.uuid4().hex[:8]}"
            inv_record = {
                "id": inv_id,
                "campus_id": campus_id,
                "email": payload.email.lower().strip(),
                "full_name": payload.full_name.strip(),
                "role": payload.role,
                "department": payload.department,
                "status": "PENDING",
                "invited_by": admin_user_id,
                "created_at": now,
                "expires_at": now + timedelta(days=7)
            }
            db.invitations[inv_id] = inv_record

            db.record_audit_event(
                actor_id=admin_user_id,
                campus_id=campus_id,
                entity_type="invitation",
                entity_id=inv_id,
                action="STAFF_INVITED",
                metadata={"email": payload.email, "role": payload.role, "department": payload.department}
            )

            return InvitationResponse(**inv_record)

    @staticmethod
    def list_invitations(campus_id: str) -> List[InvitationResponse]:
        with db._lock:
            invs = [inv for inv in db.invitations.values() if inv.get("campus_id") == campus_id]
            return [InvitationResponse(**inv) for inv in invs]

    @staticmethod
    def get_invitation(campus_id: str, invitation_id: str) -> InvitationResponse:
        with db._lock:
            inv = db.invitations.get(invitation_id)
            if not inv or inv.get("campus_id") != campus_id:
                raise HTTPException(status_code=404, detail="Invitation not found")
            return InvitationResponse(**inv)

    @staticmethod
    def update_membership(campus_id: str, admin_user_id: str, target_user_id: str, payload: MembershipUpdateRequest) -> UserItemResponse:
        with db._lock:
            u = db.users.get(target_user_id)
            if not u or u.get("campus_id") != campus_id:
                raise HTTPException(status_code=404, detail="User membership not found")

            changes = {}
            if payload.is_active is not None:
                u["is_active"] = payload.is_active
                changes["is_active"] = payload.is_active
            if payload.roles is not None:
                u["roles"] = payload.roles
                changes["roles"] = payload.roles
            if payload.department is not None:
                u["department"] = payload.department
                changes["department"] = payload.department

            u["updated_at"] = utc_now()

            db.record_audit_event(
                actor_id=admin_user_id,
                campus_id=campus_id,
                entity_type="membership",
                entity_id=target_user_id,
                action="MEMBERSHIP_UPDATED",
                metadata=changes
            )

            return UserItemResponse(
                id=u.get("id"),
                email=u.get("email"),
                full_name=u.get("full_name"),
                roles=u.get("roles", []),
                campus_id=u.get("campus_id"),
                department=u.get("department"),
                is_active=u.get("is_active", True),
                created_at=u.get("created_at"),
                updated_at=u.get("updated_at")
            )

    # ----------------------------------------------------
    # C. CAMPUS MANAGEMENT
    # ----------------------------------------------------
    @staticmethod
    def get_campus_details(campus_id: str) -> CampusDetailResponse:
        with db._lock:
            c = db.campuses.get(campus_id)
            if not c:
                raise HTTPException(status_code=404, detail="Campus not found")
            active_members = sum(1 for u in db.users.values() if u.get("campus_id") == campus_id and u.get("is_active", True))
            return CampusDetailResponse(
                id=c.get("id"),
                name=c.get("name"),
                code=c.get("code"),
                created_at=c.get("created_at"),
                configuration=c.get("configuration", {
                    "early_warning_threshold": "HIGH",
                    "sla_acceptance_days": 3,
                    "allow_counsellor_self_assignment": True
                }),
                active_members_count=active_members
            )

    @staticmethod
    def update_campus(campus_id: str, admin_user_id: str, payload: CampusUpdateRequest) -> CampusDetailResponse:
        with db._lock:
            c = db.campuses.get(campus_id)
            if not c:
                raise HTTPException(status_code=404, detail="Campus not found")

            changes = {}
            if payload.name:
                c["name"] = payload.name
                changes["name"] = payload.name
            if payload.code:
                c["code"] = payload.code
                changes["code"] = payload.code
            if payload.configuration:
                c.setdefault("configuration", {}).update(payload.configuration)
                changes["configuration"] = payload.configuration

            db.record_audit_event(
                actor_id=admin_user_id,
                campus_id=campus_id,
                entity_type="campus",
                entity_id=campus_id,
                action="CAMPUS_UPDATED",
                metadata=changes
            )
            active_members = sum(1 for u in db.users.values() if u.get("campus_id") == campus_id and u.get("is_active", True))
            return CampusDetailResponse(
                id=c.get("id"),
                name=c.get("name"),
                code=c.get("code"),
                created_at=c.get("created_at"),
                configuration=c.get("configuration"),
                active_members_count=active_members
            )

    @staticmethod
    def get_campus_activity(campus_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with db._lock:
            return [
                event for event in reversed(db.audit_log)
                if event.get("campus_id") == campus_id
            ][:limit]

    # ----------------------------------------------------
    # D. CASE SUPERVISION
    # ----------------------------------------------------
    @staticmethod
    def list_cases(
        campus_id: str,
        priority: Optional[str] = None,
        state: Optional[str] = None,
        counsellor_id: Optional[str] = None,
        overdue_only: bool = False,
        search: Optional[str] = None
    ) -> List[AdminCaseListItem]:
        now = utc_now()
        with db._lock:
            items: List[AdminCaseListItem] = []
            for case in db.cases.values():
                if case.get("institution_id") != campus_id:
                    continue
                if priority and case.get("priority") != priority:
                    continue
                if state and case.get("state") != state:
                    continue
                if counsellor_id and case.get("primary_owner_user_id") != counsellor_id:
                    continue

                due_at = case.get("due_at")
                is_overdue = bool(due_at and due_at < now and case.get("state") not in (CaseState.CLOSED.value, CaseState.DISMISSED.value))

                if overdue_only and not is_overdue:
                    continue

                student = db.students.get(case.get("student_id"), {})
                counsellor = db.users.get(case.get("primary_owner_user_id"), {})

                if search:
                    s_lower = search.lower()
                    stu_name = student.get("display_name", "").lower()
                    stu_ref = student.get("external_ref", "").lower()
                    c_id = case.get("id", "").lower()
                    if s_lower not in stu_name and s_lower not in stu_ref and s_lower not in c_id:
                        continue

                items.append(
                    AdminCaseListItem(
                        id=case.get("id"),
                        student_id=case.get("student_id"),
                        student_name=student.get("display_name"),
                        student_ref=student.get("external_ref"),
                        department=student.get("department"),
                        priority=case.get("priority"),
                        state=case.get("state"),
                        primary_owner_user_id=case.get("primary_owner_user_id"),
                        counsellor_name=counsellor.get("full_name"),
                        due_at=due_at,
                        is_overdue=is_overdue,
                        is_escalated=case.get("is_escalated", False),
                        selected_intervention_key=case.get("selected_intervention_key"),
                        version=case.get("version", 1),
                        created_at=case.get("created_at"),
                        updated_at=case.get("updated_at")
                    )
                )

            return items

    @staticmethod
    def get_case_detail(campus_id: str, case_id: str) -> AdminCaseDetail:
        now = utc_now()
        with db._lock:
            case = db.cases.get(case_id)
            if not case or case.get("institution_id") != campus_id:
                raise HTTPException(status_code=404, detail="Case record not found in this campus")

            student = db.students.get(case.get("student_id"), {})
            counsellor = db.users.get(case.get("primary_owner_user_id"), {})
            catalog_item = db.intervention_catalog.get(case.get("selected_intervention_key"), {})

            due_at = case.get("due_at")
            is_overdue = bool(due_at and due_at < now and case.get("state") not in (CaseState.CLOSED.value, CaseState.DISMISSED.value))

            # Non-confidential interventions & follow-ups
            case_interventions = [
                cat for cat in db.intervention_catalog.values()
                if cat.get("intervention_key") == case.get("selected_intervention_key")
            ]
            case_followups = [
                fu for fu in db.follow_ups.values()
                if fu.get("case_id") == case_id
            ]
            # Case lifecycle events (timeline)
            timeline_events = [
                evt for evt in db.case_events
                if evt.get("case_id") == case_id
            ]

            return AdminCaseDetail(
                id=case.get("id"),
                campus_id=case.get("institution_id"),
                student_id=case.get("student_id"),
                student_name=student.get("display_name"),
                student_ref=student.get("external_ref"),
                department=student.get("department"),
                priority=case.get("priority"),
                state=case.get("state"),
                primary_owner_user_id=case.get("primary_owner_user_id"),
                counsellor_name=counsellor.get("full_name"),
                due_at=due_at,
                is_overdue=is_overdue,
                is_escalated=case.get("is_escalated", False),
                selected_intervention_key=case.get("selected_intervention_key"),
                intervention_label=catalog_item.get("display_label"),
                version=case.get("version", 1),
                created_at=case.get("created_at"),
                updated_at=case.get("updated_at"),
                interventions=case_interventions,
                follow_ups=case_followups,
                timeline_events=timeline_events
            )

    @staticmethod
    def reassign_case(campus_id: str, admin_user_id: str, case_id: str, payload: ReassignCaseRequest) -> AdminCaseDetail:
        now = utc_now()
        with db._lock:
            case = db.cases.get(case_id)
            if not case or case.get("institution_id") != campus_id:
                raise HTTPException(status_code=404, detail="Case record not found in this campus")

            if case.get("version") != payload.expected_version:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Optimistic lock conflict: Case was modified concurrently. Expected version {payload.expected_version}, actual is {case.get('version')}"
                )

            # Validate target counsellor exists and belongs to this campus
            new_counsellor = db.users.get(payload.new_counsellor_user_id)
            if not new_counsellor or new_counsellor.get("campus_id") != campus_id or Role.COUNSELLOR.value not in new_counsellor.get("roles", []):
                raise HTTPException(status_code=400, detail="Target user must be a valid registered counsellor in this campus")

            old_counsellor_id = case.get("primary_owner_user_id")
            case["primary_owner_user_id"] = payload.new_counsellor_user_id
            case["version"] = case.get("version", 1) + 1
            case["updated_at"] = now

            # Record domain event
            db.record_case_event(
                campus_id=campus_id,
                case_id=case_id,
                actor_id=admin_user_id,
                event_type="CASE_REASSIGNED_BY_ADMIN",
                from_state=case.get("state"),
                to_state=case.get("state"),
                reason_code=payload.reassignment_reason,
                metadata={
                    "previous_counsellor_id": old_counsellor_id,
                    "new_counsellor_id": payload.new_counsellor_user_id,
                    "admin_user_id": admin_user_id
                }
            )

            # Dispatch notification to newly assigned counsellor
            notif_id = f"notif-{uuid.uuid4().hex[:8]}"
            db.notifications[notif_id] = {
                "id": notif_id,
                "user_id": payload.new_counsellor_user_id,
                "campus_id": campus_id,
                "title": "Case Transferred to You by Administrator",
                "message": f"Case #{case_id} was reassigned to you. Reason: {payload.reassignment_reason}",
                "category": NotificationCategory.CASE_ASSIGNED.value,
                "reference_type": "case",
                "reference_id": case_id,
                "is_read": False,
                "created_at": now
            }

            return AdminService.get_case_detail(campus_id, case_id)

    # ----------------------------------------------------
    # E. DATA IMPORTS
    # ----------------------------------------------------
    @staticmethod
    def list_imports(campus_id: str) -> List[ImportJobResponse]:
        with db._lock:
            return [
                ImportJobResponse(**job)
                for job in reversed(list(db.imports.values()))
                if job.get("campus_id") == campus_id
            ]

    @staticmethod
    def get_import_details(campus_id: str, import_id: str) -> ImportJobResponse:
        with db._lock:
            job = db.imports.get(import_id)
            if not job or job.get("campus_id") != campus_id:
                raise HTTPException(status_code=404, detail="Import job not found")
            return ImportJobResponse(**job)

    # ----------------------------------------------------
    # F. ANALYTICS & REPORTS
    # ----------------------------------------------------
    @staticmethod
    def get_analytics_overview(campus_id: str) -> AnalyticsOverviewResponse:
        now = utc_now()
        with db._lock:
            campus_cases = [c for c in db.cases.values() if c.get("institution_id") == campus_id]
            priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            state_counts: Dict[str, int] = {}
            resolved_count = 0
            overdue_count = 0

            for c in campus_cases:
                p = c.get("priority", "medium").lower()
                priority_counts[p] = priority_counts.get(p, 0) + 1

                s = c.get("state")
                state_counts[s] = state_counts.get(s, 0) + 1

                if s in (CaseState.CLOSED.value, CaseState.DISMISSED.value):
                    resolved_count += 1
                elif c.get("due_at") and c.get("due_at") < now:
                    overdue_count += 1

            total_cases = len(campus_cases)
            resolution_rate = round((resolved_count / total_cases * 100), 2) if total_cases > 0 else 0.0
            overdue_rate = round((overdue_count / total_cases * 100), 2) if total_cases > 0 else 0.0

            # Counsellor distribution
            counsellors = [u for u in db.users.values() if u.get("campus_id") == campus_id and Role.COUNSELLOR.value in u.get("roles", [])]
            c_dist = []
            for cr in counsellors:
                c_id = cr.get("id")
                active = sum(1 for c in campus_cases if c.get("primary_owner_user_id") == c_id and c.get("state") not in (CaseState.CLOSED.value, CaseState.DISMISSED.value))
                c_dist.append({"counsellor_id": c_id, "name": cr.get("full_name"), "active_cases": active})

            return AnalyticsOverviewResponse(
                campus_id=campus_id,
                case_volume_by_priority=priority_counts,
                case_volume_by_state=state_counts,
                counsellor_distribution=c_dist,
                resolution_rate_pct=resolution_rate,
                overdue_rate_pct=overdue_rate,
                total_interventions_catalogued=len(db.intervention_catalog),
                total_imports_run=sum(1 for j in db.imports.values() if j.get("campus_id") == campus_id)
            )

    # ----------------------------------------------------
    # G. AUDIT LOGS
    # ----------------------------------------------------
    @staticmethod
    def list_audit_events(
        campus_id: str,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLogItemResponse]:
        with db._lock:
            events = []
            for ev in reversed(db.audit_log):
                if ev.get("campus_id") != campus_id:
                    continue
                if entity_type and ev.get("entity_type") != entity_type:
                    continue
                if action and ev.get("action") != action:
                    continue
                if actor_id and ev.get("actor_id") != actor_id:
                    continue
                events.append(AuditLogItemResponse(**ev))
                if len(events) >= limit:
                    break
            return events

    # ----------------------------------------------------
    # H. ADMIN PROFILE
    # ----------------------------------------------------
    @staticmethod
    def get_profile(campus_id: str, user_id: str) -> AdminProfileResponse:
        with db._lock:
            u = db.users.get(user_id)
            if not u:
                raise HTTPException(status_code=404, detail="User record not found")
            return AdminProfileResponse(
                id=u.get("id"),
                email=u.get("email"),
                full_name=u.get("full_name"),
                roles=u.get("roles", []),
                campus_id=u.get("campus_id"),
                department=u.get("department"),
                created_at=u.get("created_at")
            )

    @staticmethod
    def update_profile(campus_id: str, user_id: str, payload: AdminProfileUpdateRequest) -> AdminProfileResponse:
        with db._lock:
            u = db.users.get(user_id)
            if not u:
                raise HTTPException(status_code=404, detail="User record not found")
            if payload.full_name:
                u["full_name"] = payload.full_name
            if payload.department is not None:
                u["department"] = payload.department
            u["updated_at"] = utc_now()

            db.record_audit_event(
                actor_id=user_id,
                campus_id=campus_id,
                entity_type="user_profile",
                entity_id=user_id,
                action="PROFILE_UPDATED",
                metadata={"full_name": u.get("full_name"), "department": u.get("department")}
            )
            return AdminProfileResponse(
                id=u.get("id"),
                email=u.get("email"),
                full_name=u.get("full_name"),
                roles=u.get("roles", []),
                campus_id=u.get("campus_id"),
                department=u.get("department"),
                created_at=u.get("created_at")
            )

    @staticmethod
    def change_password(campus_id: str, user_id: str, payload: AdminChangePasswordRequest) -> Dict[str, str]:
        with db._lock:
            u = db.users.get(user_id)
            if not u:
                raise HTTPException(status_code=404, detail="User record not found")
            if not verify_password(payload.current_password, u.get("password_hash")):
                raise HTTPException(status_code=400, detail="Current password verification failed")

            u["password_hash"] = get_password_hash(payload.new_password)
            u["updated_at"] = utc_now()

            db.record_audit_event(
                actor_id=user_id,
                campus_id=campus_id,
                entity_type="user_security",
                entity_id=user_id,
                action="PASSWORD_CHANGED",
                metadata={"status": "SUCCESS"}
            )
            return {"status": "success", "message": "Password updated successfully"}
