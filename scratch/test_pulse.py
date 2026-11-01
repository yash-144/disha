import os
import sys

# Ensure backend directory is in path
backend_path = os.path.abspath("backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.modules.pulse.services import pulse_service
from app.modules.pulse.intervention_engine import intervention_engine

def test_pulse_system():
    # 1. Test Question Generation
    gen = pulse_service.generate_randomized_questions(course_id='CS201', academic_count=5, feedback_count=4, wellbeing_count=3)
    print(f'Total generated: {gen.total_questions}')
    print(f'Academic count: {len(gen.academic_questions)}')
    print(f'Feedback count: {len(gen.feedback_questions)}')
    print(f'Wellbeing count: {len(gen.wellbeing_questions)}')
    assert gen.total_questions == 12, "Must generate exactly 12 questions"
    
    # Check no duplicate IDs
    all_ids = [q.id for q in gen.academic_questions + gen.feedback_questions + gen.wellbeing_questions]
    assert len(all_ids) == len(set(all_ids)), "Duplicate question IDs found!"

    # 2. Test 8-Scenario Intervention Matrix
    scenarios = [
        (45, 80, 85, ['Peer mentor invitation']),
        (50, 40, 75, ['Peer mentor invitation', 'Faculty review required']),
        (55, 75, 45, ['Peer mentor invitation', 'Counsellor support offer']),
        (40, 35, 30, ['Peer mentor invitation', 'Counsellor support offer', 'Faculty review required']),
        (85, 45, 80, ['Faculty review required']),
        (90, 75, 40, ['Counsellor support offer']),
        (80, 50, 45, ['Counsellor support offer', 'Faculty review required']),
        (85, 80, 90, ['No intervention needed']),
    ]

    for idx, (acad, feed, well, expected) in enumerate(scenarios):
        # Create fresh engine instance to avoid duplicate suppression in testing
        from app.modules.pulse.intervention_engine import InterventionEngine
        engine = InterventionEngine()
        res = engine.evaluate_scores(f'student-{idx}', f'Student {idx}', 'CS201', 'pulse-01', acad, feed, well)
        assert res['recommended_actions'] == expected, f"Scenario {idx+1} failed: got {res['recommended_actions']}, expected {expected}"
        print(f"Scenario {idx+1} (Acad={acad}, Feed={feed}, Well={well}) -> {res['recommended_actions']} PASSED")

    print("\nALL 8 INTERVENTION MATRIX SCENARIOS PASSED VERIFICATION!")

if __name__ == '__main__':
    test_pulse_system()
