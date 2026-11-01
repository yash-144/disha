from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SupportRequestCreate(BaseModel):
    faculty_id: str
    category: str
    preferred_slot: str
    student_note: str
    course_id: Optional[str] = None


class SupportRequestResponse(BaseModel):
    id: str
    faculty_id: str
    course_id: Optional[str] = None
    category: str
    preferred_slot: str
    student_note: str
    status: str
    faculty_response: Optional[str] = None
    created_at: datetime


class StudentProfileResponse(BaseModel):
    id: str
    student_uid: str
    display_name: str
    full_name: str
    email: Optional[str] = None
    department: Optional[str] = None
    cohort_code: Optional[str] = None
    attendance_rate: float
    quiz_score_avg: float
    enrollment_status: str


class StudentDashboardResponse(BaseModel):
    student_summary: Dict[str, Any]
    courses: List[Dict[str, Any]]
    attendance_rate: float
    quiz_score_avg: float
