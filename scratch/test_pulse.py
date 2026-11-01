import sys
import os

# Add backend directory to sys.path
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.modules.pulse.question_bank import COURSE_QUESTION_BANK
from app.modules.pulse.services import pulse_service
from app.modules.pulse.intervention_engine import pulse_intervention_engine

print(f"Total questions in bank: {len(COURSE_QUESTION_BANK)}")
acad = [q for q in COURSE_QUESTION_BANK if q["category"] == "ACADEMIC"]
feed = [q for q in COURSE_QUESTION_BANK if q["category"] == "CLASSROOM_FEEDBACK"]
well = [q for q in COURSE_QUESTION_BANK if q["category"] == "WELLBEING"]
print(f"Academic: {len(acad)}, Feedback: {len(feed)}, Wellbeing: {len(well)}")

# Test randomization
gen = pulse_service.generate_randomized_questions(course_id="CS201")
print(f"Generated: {gen.total_questions} questions across {len(gen.academic_questions)} acad, {len(gen.feedback_questions)} feed, {len(gen.wellbeing_questions)} well")

# Test 5 intervention matrix scenarios:
print("\n--- Testing 5 Intervention Matrix Scenarios ---")

# Scenario 1: Low academic (<60%), healthy others (>=60%) -> Peer mentor invitation
s1 = pulse_intervention_engine.evaluate_interventions(
    submission_id="sub-test-01",
    student_id="student-test-01",
    pulse_id="pulse-test-01",
    course_id="CS201",
    academic_score=40.0,
    feedback_score=80.0,
    wellbeing_score=75.0
)
print("Scenario 1 (Low Acad, Healthy others):", s1["recommended_actions"])
assert "PEER_MENTOR_INVITATION" in s1["recommended_actions"]
assert "COUNSELLOR_OFFER" not in s1["recommended_actions"]

# Scenario 2: Healthy academics (>=60%), low wellbeing (<60%) -> Counselling offer
s2 = pulse_intervention_engine.evaluate_interventions(
    submission_id="sub-test-02",
    student_id="student-test-02",
    pulse_id="pulse-test-01",
    course_id="CS201",
    academic_score=85.0,
    feedback_score=80.0,
    wellbeing_score=45.0
)
print("Scenario 2 (Healthy Acad, Low Wellbeing):", s2["recommended_actions"])
assert "COUNSELLOR_OFFER" in s2["recommended_actions"]
assert "PEER_MENTOR_INVITATION" not in s2["recommended_actions"]

# Scenario 3: Low across all categories (<60%) -> Peer mentor + Counsellor + Faculty Review
s3 = pulse_intervention_engine.evaluate_interventions(
    submission_id="sub-test-03",
    student_id="student-test-03",
    pulse_id="pulse-test-01",
    course_id="CS201",
    academic_score=35.0,
    feedback_score=45.0,
    wellbeing_score=40.0
)
print("Scenario 3 (Low across all):", s3["recommended_actions"])
assert "PEER_MENTOR_INVITATION" in s3["recommended_actions"]
assert "COUNSELLOR_OFFER" in s3["recommended_actions"]
assert "FACULTY_REVIEW" in s3["recommended_actions"]

# Scenario 4: Healthy across all categories (>=60%) -> No intervention
s4 = pulse_intervention_engine.evaluate_interventions(
    submission_id="sub-test-04",
    student_id="student-test-04",
    pulse_id="pulse-test-01",
    course_id="CS201",
    academic_score=90.0,
    feedback_score=85.0,
    wellbeing_score=80.0
)
print("Scenario 4 (Healthy across all):", s4["recommended_actions"])
assert len(s4["recommended_actions"]) == 0

# Scenario 5: Low classroom feedback (<60%), healthy others -> Faculty review
s5 = pulse_intervention_engine.evaluate_interventions(
    submission_id="sub-test-05",
    student_id="student-test-05",
    pulse_id="pulse-test-01",
    course_id="CS201",
    academic_score=80.0,
    feedback_score=45.0,
    wellbeing_score=75.0
)
print("Scenario 5 (Low Feedback):", s5["recommended_actions"])
assert s5["recommended_actions"] == ["FACULTY_REVIEW"]

print("\nALL BACKEND PULSE UNIT TESTS PASSED!")

