from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DISHA_DATABASE_URL,
    echo=(settings.DISHA_ENV == "development"),
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
import uuid
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from app.core.security import get_password_hash
from app.shared.enums import CaseState, CasePriority, FollowUpStatus, OutcomeStatus, NotificationCategory
from app.shared.utils import compute_hash, utc_now

class DataStore:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataStore, cls).__new__(cls)
                cls._instance._init_tables()
                cls._instance._seed_data()
            return cls._instance

    def _init_tables(self):
        self.campuses: Dict[str, dict] = {}
        self.users: Dict[str, dict] = {}
        self.invitations: Dict[str, dict] = {}
        self.counselor_profiles: Dict[str, dict] = {}
        self.students: Dict[str, dict] = {}
        self.observations: Dict[str, dict] = {}
        self.intervention_catalog: Dict[str, dict] = {}
        self.cases: Dict[str, dict] = {}
        self.case_events: List[dict] = []
        self.case_notes: Dict[str, dict] = {}
        self.counselling_notes: Dict[str, dict] = {}
        self.follow_ups: Dict[str, dict] = {}
        self.case_outcomes: Dict[str, dict] = {}
        self.notifications: Dict[str, dict] = {}
        self.imports: Dict[str, dict] = {}
        self.audit_log: List[dict] = []
        self._last_audit_hash: str = "0" * 64

    def reset(self):
        """Reset data store for testing clean isolation."""
        with self._lock:
            self._init_tables()
            self._seed_data()

    def _seed_data(self):
        # 1. Campus
        campus_id = "campus-ipp-01"
        self.campuses[campus_id] = {
            "id": campus_id,
            "name": "Polytechnic Institute of Portalegre",
            "code": "IPP-PORTALEGRE",
            "created_at": utc_now()
        }

        # 2. Users
        # Main Counsellor
        counselor_user_id = "user-counselor-01"
        self.users[counselor_user_id] = {
            "id": counselor_user_id,
            "email": "counselor.disha@institution.edu",
            "password_hash": get_password_hash("DishaCounsellor@2026"),
            "full_name": "Dr. Elena Rostova",
            "roles": ["counsellor"],
            "campus_id": campus_id,
            "created_at": utc_now()
        }

        # Secondary Counsellor (for authorization isolation tests)
        other_counselor_id = "user-counselor-02"
        self.users[other_counselor_id] = {
            "id": other_counselor_id,
            "email": "counselor.other@institution.edu",
            "password_hash": get_password_hash("OtherCounsellor@2026"),
            "full_name": "Dr. Marcus Vance",
            "roles": ["counsellor"],
            "campus_id": campus_id,
            "created_at": utc_now()
        }

        # Faculty User
        faculty_user_id = "user-faculty-01"
        self.users[faculty_user_id] = {
            "id": faculty_user_id,
            "email": "faculty.john@institution.edu",
            "password_hash": get_password_hash("FacultyPass@2026"),
            "full_name": "Prof. Johnathan Myers",
            "roles": ["faculty"],
            "campus_id": campus_id,
            "created_at": utc_now()
        }

        # Student User
        student_user_id = "user-student-01"
        self.users[student_user_id] = {
            "id": student_user_id,
            "email": "student.ana@institution.edu",
            "password_hash": get_password_hash("StudentPass@2026"),
            "full_name": "Ana Silva",
            "roles": ["student"],
            "campus_id": campus_id,
            "created_at": utc_now()
        }

        # Institution Administrator User
        admin_user_id = "user-admin-01"
        self.users[admin_user_id] = {
            "id": admin_user_id,
            "email": "admin.disha@institution.edu",
            "password_hash": get_password_hash("DishaAdmin@2026"),
            "full_name": "Dr. Sarah Jenkins",
            "roles": ["institution_admin"],
            "campus_id": campus_id,
            "department": "Campus Administration",
            "is_active": True,
            "created_at": utc_now()
        }

        # Platform Administrator User
        platform_admin_id = "user-platform-admin-01"
        self.users[platform_admin_id] = {
            "id": platform_admin_id,
            "email": "platform.admin@disha.edu",
            "password_hash": get_password_hash("PlatformAdmin@2026"),
            "full_name": "Alexander Sterling",
            "roles": ["platform_admin"],
            "campus_id": campus_id,
            "department": "Platform Operations",
            "is_active": True,
            "created_at": utc_now()
        }

        # Pre-seed initial sample imports
        import_1_id = "import-001"
        self.imports[import_1_id] = {
            "id": import_1_id,
            "campus_id": campus_id,
            "file_name": "uci_student_dropout_batch_1.csv",
            "source_type": "STUDENT_ROSTER",
            "status": "COMPLETED",
            "total_records": 120,
            "processed_records": 120,
            "error_count": 0,
            "errors": [],
            "created_by": admin_user_id,
            "created_at": utc_now() - timedelta(days=5),
            "completed_at": utc_now() - timedelta(days=5)
        }
        import_2_id = "import-002"
        self.imports[import_2_id] = {
            "id": import_2_id,
            "campus_id": campus_id,
            "file_name": "attendance_records_oct_2026.csv",
            "source_type": "ATTENDANCE_LOGS",
            "status": "COMPLETED_WITH_WARNINGS",
            "total_records": 85,
            "processed_records": 82,
            "error_count": 3,
            "errors": [
                {"row": 14, "column": "student_uid", "error": "Unknown student identifier STU-9999", "raw_value": "STU-9999"},
                {"row": 32, "column": "attendance_pct", "error": "Percentage value > 100", "raw_value": "112"},
                {"row": 59, "column": "date", "error": "Invalid ISO timestamp format", "raw_value": "2026/10/32"}
            ],
            "created_by": admin_user_id,
            "created_at": utc_now() - timedelta(days=2),
            "completed_at": utc_now() - timedelta(days=2)
        }

        # Pre-seed an initial invitation
        inv_1_id = "inv-001"
        self.invitations[inv_1_id] = {
            "id": inv_1_id,
            "campus_id": campus_id,
            "email": "dr.martins.counsel@institution.edu",
            "full_name": "Dr. Sofia Martins",
            "role": "counsellor",
            "department": "Student Welfare",
            "status": "PENDING",
            "invited_by": admin_user_id,
            "created_at": utc_now() - timedelta(days=3),
            "expires_at": utc_now() + timedelta(days=4)
        }

        # 3. Counselor Profile
        self.counselor_profiles[counselor_user_id] = {
            "id": f"prof-{counselor_user_id}",
            "user_id": counselor_user_id,
            "campus_id": campus_id,
            "full_name": "Dr. Elena Rostova",
            "email": "counselor.disha@institution.edu",
            "phone": "+351-912-345-678",
            "designation": "Senior Student Wellbeing Counsellor",
            "department": "Student Affairs & Guidance",
            "specializations": ["Academic Anxiety", "Attendance Intervention", "Career Direction"],
            "qualification": "Ph.D. in Educational Psychology",
            "availability_status": "available",
            "assigned_cohorts": ["CS-2024", "BIO-2025", "ENG-2024"],
            "onboarding_status": "VERIFIED",
            "created_at": utc_now(),
            "updated_at": utc_now()
        }

        # 4. Students (Matching UCI dataset profiles)
        student_1_id = "student-001"
        self.students[student_1_id] = {
            "id": student_1_id,
            "institution_id": campus_id,
            "external_ref": "STU-2024-9070",
            "display_name": "Ana Silva",
            "department": "Computer Science & Informatics",
            "course": "Software Engineering (Code 9070)",
            "cohort_code": "CS-2024",
            "academic_year": "Year 2",
            "enrollment_status": "active",
            "created_at": utc_now()
        }

        student_2_id = "student-002"
        self.students[student_2_id] = {
            "id": student_2_id,
            "institution_id": campus_id,
            "external_ref": "STU-2024-9254",
            "display_name": "Bernardo Costa",
            "department": "Biomedical Sciences",
            "course": "Nursing (Code 9254)",
            "cohort_code": "BIO-2025",
            "academic_year": "Year 1",
            "enrollment_status": "active",
            "created_at": utc_now()
        }

        student_3_id = "student-003"
        self.students[student_3_id] = {
            "id": student_3_id,
            "institution_id": campus_id,
            "external_ref": "STU-2024-9500",
            "display_name": "Carla Mendonca",
            "department": "Management & Economics",
            "course": "Economics & Administration (Code 9500)",
            "cohort_code": "ENG-2024",
            "academic_year": "Year 3",
            "enrollment_status": "active",
            "created_at": utc_now()
        }

        # 5. Observations (Evidence)
        self.observations["obs-001"] = {
            "id": "obs-001",
            "institution_id": campus_id,
            "student_id": student_1_id,
            "domain": "attendance",
            "title": "Semester 1 Lecture Absence Spike",
            "value": "Attendance dropped to 58% in Data Structures",
            "event_at": utc_now() - timedelta(days=14),
            "quality_state": "valid",
            "provenance": "IPP-Campus-Attendance-Gateway-v1"
        }
        self.observations["obs-002"] = {
            "id": "obs-002",
            "institution_id": campus_id,
            "student_id": student_1_id,
            "domain": "academic",
            "title": "Midterm Examination Evaluation",
            "value": "Score: 7.5/20 in Curricular Unit 1st Sem",
            "event_at": utc_now() - timedelta(days=10),
            "quality_state": "valid",
            "provenance": "Academic-Records-DGES-Sync"
        }

        # 6. Intervention Catalogue
        catalogue_items = [
            ("ACADEMIC_PEER_TUTORING", "Academic Tutoring", "academic", "1-on-1 subject tutoring with certified senior peer tutor"),
            ("COUNSELLOR_INTAKE_MEETING", "Counselling Consultation", "counselling", "Direct therapeutic assessment and personal guidance consultation"),
            ("STUDY_SKILLS_WORKSHOP", "Study Skills Program", "skills", "Time management, exam preparation, and organizational mentorship"),
            ("FINANCIAL_AID_LIAISON", "Emergency Aid Review", "finance", "Referral for tuition payment restructuring and emergency student aid")
        ]
        for key, label, dom, desc in catalogue_items:
            self.intervention_catalog[key] = {
                "id": str(uuid.uuid4()),
                "institution_id": campus_id,
                "intervention_key": key,
                "display_label": label,
                "domain": dom,
                "description": desc,
                "active": True
            }

        # 7. Pre-seed Cases
        # Case 1: Assigned to Elena (awaiting acceptance)
        case_1_id = "case-101"
        self.cases[case_1_id] = {
            "id": case_1_id,
            "institution_id": campus_id,
            "student_id": student_1_id,
            "originating_signal_id": "sig-001",
            "selected_intervention_key": "COUNSELLOR_INTAKE_MEETING",
            "priority": CasePriority.HIGH.value,
            "state": CaseState.ASSIGNED.value,
            "primary_owner_user_id": counselor_user_id,
            "due_at": utc_now() + timedelta(days=3),
            "accepted_at": None,
            "closed_at": None,
            "closed_by": None,
            "is_escalated": False,
            "version": 1,
            "created_at": utc_now() - timedelta(days=2),
            "updated_at": utc_now() - timedelta(days=2)
        }
        self.record_case_event(
            campus_id=campus_id,
            case_id=case_1_id,
            actor_id="system",
            event_type="OWNER_ASSIGNED",
            from_state=CaseState.ACTION_PLANNED.value,
            to_state=CaseState.ASSIGNED.value,
            reason_code="ASSIGNED_TO_DEPARTMENTAL_COUNSELLOR",
            metadata={"assigned_to": counselor_user_id}
        )

        # Case 2: Active Case (accepted and support in progress)
        case_2_id = "case-102"
        self.cases[case_2_id] = {
            "id": case_2_id,
            "institution_id": campus_id,
            "student_id": student_2_id,
            "originating_signal_id": "sig-002",
            "selected_intervention_key": "STUDY_SKILLS_WORKSHOP",
            "priority": CasePriority.MEDIUM.value,
            "state": CaseState.SUPPORT_IN_PROGRESS.value,
            "primary_owner_user_id": counselor_user_id,
            "due_at": utc_now() + timedelta(days=5),
            "accepted_at": utc_now() - timedelta(days=3),
            "closed_at": None,
            "closed_by": None,
            "is_escalated": False,
            "version": 3,
            "created_at": utc_now() - timedelta(days=5),
            "updated_at": utc_now() - timedelta(days=1)
        }

        # Follow-up for Case 2
        fu_1_id = "fu-201"
        self.follow_ups[fu_1_id] = {
            "id": fu_1_id,
            "institution_id": campus_id,
            "case_id": case_2_id,
            "title": "Check-in on Week 2 Exam Preparation",
            "follow_up_type": "in_person_session",
            "contact_status": "scheduled",
            "proof_kind": "signed_attendance_slip",
            "scheduled_at": utc_now() + timedelta(days=1),
            "completed_at": None,
            "completed_by": None,
            "notes": "Verify student attended scheduled mathematics tutoring.",
            "status": FollowUpStatus.SCHEDULED.value,
            "created_at": utc_now() - timedelta(days=2)
        }

        # Case 3: Overdue Case
        case_3_id = "case-103"
        self.cases[case_3_id] = {
            "id": case_3_id,
            "institution_id": campus_id,
            "student_id": student_3_id,
            "originating_signal_id": "sig-003",
            "selected_intervention_key": "ACADEMIC_PEER_TUTORING",
            "priority": CasePriority.CRITICAL.value,
            "state": CaseState.ACCEPTED.value,
            "primary_owner_user_id": counselor_user_id,
            "due_at": utc_now() - timedelta(days=2), # Overdue
            "accepted_at": utc_now() - timedelta(days=4),
            "closed_at": None,
            "closed_by": None,
            "is_escalated": True,
            "version": 2,
            "created_at": utc_now() - timedelta(days=7),
            "updated_at": utc_now() - timedelta(days=2)
        }

        # 8. Pre-seed Notification for Elena
        notif_id = "notif-001"
        self.notifications[notif_id] = {
            "id": notif_id,
            "user_id": counselor_user_id,
            "title": "New Case Assigned: Ana Silva",
            "message": "High priority attendance intervention case assigned to your care.",
            "category": NotificationCategory.CASE_ASSIGNED.value,
            "reference_type": "case",
            "reference_id": case_1_id,
            "is_read": False,
            "created_at": utc_now() - timedelta(hours=3)
        }

    def record_case_event(
        self, campus_id: str, case_id: str, actor_id: str,
        event_type: str, from_state: Optional[str], to_state: Optional[str],
        reason_code: Optional[str] = None, metadata: Optional[dict] = None
    ) -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "institution_id": campus_id,
            "case_id": case_id,
            "actor_user_id": actor_id,
            "event_type": event_type,
            "from_state": from_state,
            "to_state": to_state,
            "reason_code": reason_code,
            "metadata": metadata or {},
            "created_at": utc_now()
        }
        self.case_events.append(event)
        
        # Mirror to platform immutable audit log
        self.record_audit_event(
            actor_id=actor_id,
            campus_id=campus_id,
            entity_type="case",
            entity_id=case_id,
            action=event_type,
            metadata={"from_state": from_state, "to_state": to_state, **(metadata or {})}
        )
        return event

    def record_audit_event(
        self, actor_id: str, campus_id: str, entity_type: str,
        entity_id: str, action: str, metadata: Optional[dict] = None
    ) -> dict:
        prev_hash = self._last_audit_hash
        event_body = {
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "campus_id": campus_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "metadata": metadata or {},
            "created_at": utc_now()
        }
        curr_hash = compute_hash(event_body, prev_hash)
        event_body["prev_hash"] = prev_hash
        event_body["curr_hash"] = curr_hash
        self._last_audit_hash = curr_hash
        self.audit_log.append(event_body)
        return event_body

# Global singleton
db = DataStore()
