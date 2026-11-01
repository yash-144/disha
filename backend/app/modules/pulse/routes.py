from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.modules.pulse.services import pulse_service
from app.modules.pulse.schemas import (
    PulseGenerateRequest,
    PulseGenerateResponse,
    PulseCreateRequest,
    PulseSubmitRequest,
    PulseSubmissionResult,
    PulseSummaryFacultyView,
)

router = APIRouter(prefix="/api/v1/pulse", tags=["Student Pulse"])


@router.post("/generate", response_model=PulseGenerateResponse)
async def generate_random_pulse(payload: PulseGenerateRequest):
    """
    Randomly select questions without replacement across the 3 categories:
    Category A (Academic), Category B (Classroom Feedback), Category C (Student Wellbeing).
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
    Instantly grades objective questions and permanently anonymizes feedback.
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


@router.get("/interventions")
async def get_interventions():
    """Retrieve all triggered interventions history."""
    from app.modules.pulse.intervention_engine import intervention_engine
    return intervention_engine.list_interventions()


@router.get("/mentors")
async def get_peer_mentors():
    """Retrieve the peer mentor pool and active availability."""
    from app.modules.pulse.intervention_engine import intervention_engine
    return intervention_engine.list_peer_mentors()


@router.post("/mentors/invitation/{invitation_id}/respond")
async def respond_to_mentor_invitation(invitation_id: str, accept: bool):
    """Student responds to a voluntary peer mentor invitation."""
    from app.modules.pulse.intervention_engine import intervention_engine
    try:
        return intervention_engine.respond_to_mentor_invitation(invitation_id, accept)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/counselling/offer/{offer_id}/respond")
async def respond_to_counselling_offer(offer_id: str, accept: bool):
    """Student responds to a private, voluntary counselling offer."""
    from app.modules.pulse.intervention_engine import intervention_engine
    try:
        return intervention_engine.respond_to_counselling_offer(offer_id, accept)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    """Returns the 5 canonical demo scenarios for evaluator verification."""
    return pulse_service.demo_scenarios

