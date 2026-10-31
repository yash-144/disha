from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PulseQuestionResponse(BaseModel):
    id: str
    course_id: str
    course_name: str
    category: str  # 'ACADEMIC' | 'CLASSROOM_FEEDBACK' | 'WELLBEING'
    prompt: str
    question_type: str  # 'mcq' | 'descriptive' | 'likert' | 'single_choice' | 'multi_choice'
    difficulty: str  # 'Easy' | 'Medium' | 'Hard'
    marks: float
    options: List[str] = []
    correct_option: Optional[int] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    parameter_tag: Optional[str] = None


class PulseQuestionStudentView(BaseModel):
    id: str
    course_id: str
    category: str
    prompt: str
    question_type: str
    difficulty: str
    marks: float
    options: List[str] = []
    parameter_tag: Optional[str] = None


class PulseGenerateRequest(BaseModel):
    course_id: str = "CS201"
    academic_count: int = Field(default=5, ge=1, le=15)
    feedback_count: int = Field(default=4, ge=1, le=10)
    wellbeing_count: int = Field(default=3, ge=1, le=10)


class PulseGenerateResponse(BaseModel):
    course_id: str
    academic_questions: List[PulseQuestionResponse]
    feedback_questions: List[PulseQuestionResponse]
    wellbeing_questions: List[PulseQuestionResponse]
    total_questions: int
    total_marks: float
    seed_token: str


class PulseCreateRequest(BaseModel):
    course_id: str = "CS201"
    section_id: str = "SEC-A"
    title: str
    status: str = "published"  # 'draft' | 'published'
    due_at: Optional[datetime] = None
    question_ids: List[str]
    academic_count: int = 5
    feedback_count: int = 4
    wellbeing_count: int = 3


class PulseSubmitRequest(BaseModel):
    student_id: str
    academic_answers: Dict[str, Any]  # { question_id: selected_index or text }
    feedback_answers: Dict[str, Any]  # { question_id: choice or rating }
    wellbeing_answers: Dict[str, Any]  # { question_id: rating }
    is_anonymous: bool = True


class ObjectiveQuestionResult(BaseModel):
    question_id: str
    prompt: str
    selected_option: Optional[Any]
    correct_option: Optional[Any]
    is_correct: bool
    marks_awarded: float
    max_marks: float
    explanation: Optional[str]


class PulseSubmissionResult(BaseModel):
    submission_id: str
    pulse_id: str
    submitted_at: datetime
    academic_score: float
    academic_max_marks: float
    percentage: float
    objective_results: List[ObjectiveQuestionResult]
    feedback_anonymized_ack: bool
    wellbeing_anonymized_ack: bool
    privacy_notice: str


class PulseSummaryFacultyView(BaseModel):
    id: str
    course_id: str
    course_name: str
    section_id: str
    title: str
    status: str
    due_at: Optional[str]
    created_at: str
    total_questions: int
    academic_count: int
    feedback_count: int
    wellbeing_count: int
    total_marks: float
    submission_count: int
    total_students: int
    avg_score_percentage: float
