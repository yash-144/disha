from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status

from app.modules.pulse.services import pulse_service
from app.modules.pulse.intervention_engine import pulse_intervention_engine
from app.modules.pulse.schemas import (
    PulseGenerateRequest,
    PulseGenerateResponse,
    PulseCreateRequest,
    PulseSubmitRequest,
    PulseSubmissionResult,
    PulseSummaryFacultyView,
    MentorResponseRequest,
    CounsellorOfferResponseRequest,
)

router = APIRouter(prefix="/api/v1/pulse", tags=["Student Pulse"])


@router.post("/generate", response_model=PulseGenerateResponse)
async def generate_random_pulse(payload: PulseGenerateRequest):
    """
    Randomly select questions without replacement across the 3 categories:
    Category A (Academic: 3 MCQs, 1 conceptual, 1 application),
    Category B (Classroom Feedback: 2 Likert, 1 single-choice, 1 optional descriptive),
    Category C (Student Wellbeing: 2 Likert, 1 single-choice).
    Faculty can call this repeatedly to preview and regenerate questions.
    """
    try:
        return pulse_service.generate_randomized_questions(
            course_id=payload.course_id,
            academic_count=payload.academic_count,
            feedback_count=payload.feedback_count,
            wellbeing_count=payload.wellbeing_count,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_pulse_assignment(payload: PulseCreateRequest):
    """
    Create and lock the randomized question set for a Student Pulse assignment.
    """
    try:
        created = pulse_service.create_pulse_assignment(
            data=payload.model_dump(),
            created_by="faculty-current-user"
        )
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/faculty/list", response_model=List[PulseSummaryFacultyView])
async def list_faculty_pulses():
    """
    Retrieve all Student Pulse assignments for the faculty member with completion stats.
    """
    return pulse_service.list_faculty_pulses()


@router.get("/faculty/{pulse_id}/analytics")
async def get_pulse_analytics(pulse_id: str):
    """
    Retrieve 3-Part Analytics for Faculty:
    1. Academic Performance (Scores, Difficulty breakdown, Item Analysis)
    2. Classroom Feedback (Aggregated pace, clarity, engagement distributions)
    3. Student Wellbeing (Cohort motivation, academic pressure, actionable suggestions, k-anonymity >= 5)
    """
    try:
        return pulse_service.get_pulse_3part_analytics(pulse_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{pulse_id}")
async def get_student_pulse_test(pulse_id: str, student_id: str = "current-student"):
    """
    Retrieve active pulse questions sanitized for student taking.
    """
    try:
        return pulse_service.get_pulse_for_student(pulse_id=pulse_id, student_id=student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/student/{pulse_id}/submit", response_model=PulseSubmissionResult)
async def submit_student_pulse(pulse_id: str, payload: PulseSubmitRequest):
    """
    Submit student answers across Academic, Classroom Feedback, and Wellbeing categories.
    Instantly grades objective questions, calculates 3 category scores, and evaluates the 8-row intervention matrix.
    """
    try:
        return pulse_service.submit_pulse_responses(
            pulse_id=pulse_id,
            student_id=payload.student_id,
            academic_answers=payload.academic_answers,
            feedback_answers=payload.feedback_answers,
            wellbeing_answers=payload.wellbeing_answers,
            is_anonymous=payload.is_anonymous,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mentors")
async def list_peer_mentors(course_id: Optional[str] = None):
    """List volunteer peer mentors in the peer mentor pool."""
    mentors = list(pulse_intervention_engine.peer_mentor_pool.values())
    if course_id:
        mentors = [m for m in mentors if course_id in m.get("eligible_courses", [])]
    return mentors


@router.post("/mentor-requests/{request_id}/respond")
async def respond_to_mentor_request(request_id: str, payload: MentorResponseRequest):
    """Accept or decline a voluntary peer mentorship invitation."""
    try:
        return pulse_intervention_engine.respond_to_mentor_request(
            request_id=request_id,
            accepted=payload.accepted
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/counsellor-offers/{offer_id}/respond")
async def respond_to_counsellor_offer(offer_id: str, payload: CounsellorOfferResponseRequest):
    """Accept or decline a private confidential counselling support offer."""
    try:
        return pulse_intervention_engine.respond_to_counsellor_offer(
            offer_id=offer_id,
            accepted=payload.accepted
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/interventions")
async def list_interventions(pulse_id: Optional[str] = None, student_id: Optional[str] = None):
    """List historical intervention records generated by the Student Pulse intervention engine."""
    records = pulse_intervention_engine.intervention_records
    if pulse_id:
        records = [r for r in records if r["pulse_id"] == pulse_id]
    if student_id:
        records = [r for r in records if r["student_id"] == student_id]
    return records


@router.get("/thresholds")
async def get_thresholds():
    """Retrieve operational scoring thresholds for Student Pulse."""
    return {
        "version": pulse_intervention_engine.VERSION,
        "thresholds": pulse_intervention_engine.threshold_configs,
        "description": "Initial operational thresholds (60.0% cutoff for Academic, Feedback, and Wellbeing)"
    }
