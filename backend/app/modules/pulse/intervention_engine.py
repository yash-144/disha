"""Backend Intervention Engine for Student Pulse.

Evaluates 3 category scores independently against the configured 60% threshold
using the canonical 8-scenario decision matrix:

| Academic | Classroom Feedback | Wellbeing | Recommended Action |
|---|---|---|---|
| Low | Good | Good | Peer mentor invitation |
| Low | Low | Good | Peer mentor + faculty review |
| Low | Good | Low | Peer mentor + counsellor offer |
| Low | Low | Low | Peer mentor + counsellor offer + faculty review |
| Good | Low | Good | Faculty review |
| Good | Good | Low | Counsellor offer |
| Good | Low | Low | Counsellor offer + faculty review |
| Good | Good | Good | No intervention |
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.services.notification_service import NotificationService
from app.shared.utils import utc_now


class InterventionEngine:
    def __init__(self):
        # Configurable thresholds
        self.thresholds = {
            "academic": 60.0,
            "feedback": 60.0,
            "wellbeing": 60.0,
            "version": "v1.0-60pct",
        }

        # Peer Mentor Pool: voluntary students with good standing
        self.peer_mentor_pool: List[Dict[str, Any]] = [
            {
                "mentor_id": "mentor-rahul-01",
                "student_id": "student-rahul",
                "display_name": "Rahul Verma",
                "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&q=80",
                "eligible_courses": ["CS201", "CS202"],
                "availability": "Weekday evenings & Saturday mornings",
                "max_capacity": 3,
                "active_mentees": 1,
                "volunteer_status": "active",
                "gpa": 9.2,
            },
            {
                "mentor_id": "mentor-priya-02",
                "student_id": "student-priya",
                "display_name": "Priya Nair",
                "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&q=80",
                "eligible_courses": ["CS201"],
                "availability": "Tuesday & Thursday 4-6 PM",
                "max_capacity": 2,
                "active_mentees": 0,
                "volunteer_status": "active",
                "gpa": 8.9,
            },
            {
                "mentor_id": "mentor-ananya-03",
                "student_id": "student-ananya",
                "display_name": "Ananya Desai",
                "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=120&q=80",
                "eligible_courses": ["CS202"],
                "availability": "Flexible weekends",
                "max_capacity": 3,
                "active_mentees": 1,
                "volunteer_status": "active",
                "gpa": 9.4,
            },
        ]

        # Active interventions store
        self.interventions_history: List[Dict[str, Any]] = []

        # Mentor invitations store
        self.mentor_invitations: Dict[str, Dict[str, Any]] = {}

        # Counselling offers store
        self.counselling_offers: Dict[str, Dict[str, Any]] = {}

    def get_thresholds(self) -> Dict[str, Any]:
        return dict(self.thresholds)

    def set_thresholds(self, academic: float, feedback: float, wellbeing: float) -> Dict[str, Any]:
        self.thresholds["academic"] = academic
        self.thresholds["feedback"] = feedback
        self.thresholds["wellbeing"] = wellbeing
        return self.thresholds

    def evaluate_scores(
        self,
        student_id: str,
        student_name: str,
        course_id: str,
        pulse_id: str,
        academic_score: float,
        feedback_score: float,
        wellbeing_score: float,
    ) -> Dict[str, Any]:
        """
        Evaluate the 3 category scores against thresholds and trigger interventions.
        Enforces duplicate prevention for the same unresolved risk.
        """
        acad_status = "Good" if academic_score >= self.thresholds["academic"] else "Low"
        feed_status = "Good" if feedback_score >= self.thresholds["feedback"] else "Low"
        well_status = "Good" if wellbeing_score >= self.thresholds["wellbeing"] else "Low"

        # Check existing active intervention to prevent duplicate spam
        existing = next(
            (
                item
                for item in self.interventions_history
                if item["student_id"] == student_id
                and item["course_id"] == course_id
                and item["status"] in ["pending_action", "accepted"]
            ),
            None,
        )

        # Exact 8-scenario decision matrix
        recommended_actions = []
        requires_mentor = False
        requires_counsellor = False
        requires_faculty_review = False

        if acad_status == "Low" and feed_status == "Good" and well_status == "Good":
            recommended_actions.append("Peer mentor invitation")
            requires_mentor = True
        elif acad_status == "Low" and feed_status == "Low" and well_status == "Good":
            recommended_actions.append("Peer mentor invitation")
            recommended_actions.append("Faculty review required")
            requires_mentor = True
            requires_faculty_review = True
        elif acad_status == "Low" and feed_status == "Good" and well_status == "Low":
            recommended_actions.append("Peer mentor invitation")
            recommended_actions.append("Counsellor support offer")
            requires_mentor = True
            requires_counsellor = True
        elif acad_status == "Low" and feed_status == "Low" and well_status == "Low":
            recommended_actions.append("Peer mentor invitation")
            recommended_actions.append("Counsellor support offer")
            recommended_actions.append("Faculty review required")
            requires_mentor = True
            requires_counsellor = True
            requires_faculty_review = True
        elif acad_status == "Good" and feed_status == "Low" and well_status == "Good":
            recommended_actions.append("Faculty review required")
            requires_faculty_review = True
        elif acad_status == "Good" and feed_status == "Good" and well_status == "Low":
            recommended_actions.append("Counsellor support offer")
            requires_counsellor = True
        elif acad_status == "Good" and feed_status == "Low" and well_status == "Low":
            recommended_actions.append("Counsellor support offer")
            recommended_actions.append("Faculty review required")
            requires_counsellor = True
            requires_faculty_review = True
        else:
            # Good across all 3
            recommended_actions.append("No intervention needed")

        action_summary = " + ".join(recommended_actions)

        intervention_id = f"intv-{uuid.uuid4().hex[:8]}"
        record = {
            "intervention_id": intervention_id,
            "student_id": student_id,
            "student_name": student_name,
            "course_id": course_id,
            "pulse_id": pulse_id,
            "scores": {
                "academic": academic_score,
                "feedback": feedback_score,
                "wellbeing": wellbeing_score,
            },
            "status_flags": {
                "academic": acad_status,
                "feedback": feed_status,
                "wellbeing": well_status,
            },
            "thresholds_applied": dict(self.thresholds),
            "recommended_actions": recommended_actions,
            "action_summary": action_summary,
            "requires_mentor": requires_mentor,
            "requires_counsellor": requires_counsellor,
            "requires_faculty_review": requires_faculty_review,
            "status": "pending_action" if (requires_mentor or requires_counsellor or requires_faculty_review) else "resolved",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mentor_invitation_id": None,
            "counselling_offer_id": None,
        }

        # 1. Trigger Peer Mentorship Matching
        if requires_mentor and not (existing and existing.get("requires_mentor")):
            inv = self._create_mentor_invitation(student_id, student_name, course_id, intervention_id)
            record["mentor_invitation_id"] = inv["invitation_id"]
            record["matched_mentor"] = inv["mentor_name"]

        # 2. Trigger Counsellor Offer (Voluntary, private)
        if requires_counsellor and not (existing and existing.get("requires_counsellor")):
            off = self._create_counselling_offer(student_id, student_name, intervention_id)
            record["counselling_offer_id"] = off["offer_id"]

        # 3. Trigger Faculty Review Alert
        if requires_faculty_review:
            self._notify_faculty_review(student_name, course_id, feed_status, acad_status)

        self.interventions_history.append(record)
        return record

    def _create_mentor_invitation(
        self, student_id: str, student_name: str, course_id: str, intervention_id: str
    ) -> Dict[str, Any]:
        """Match an available peer mentor for the subject and notify both."""
        # Find eligible mentor with available capacity
        eligible = [
            m
            for m in self.peer_mentor_pool
            if course_id in m["eligible_courses"] and m["active_mentees"] < m["max_capacity"]
        ]
        assigned_mentor = eligible[0] if eligible else self.peer_mentor_pool[0]

        inv_id = f"minv-{uuid.uuid4().hex[:8]}"
        invitation = {
            "invitation_id": inv_id,
            "intervention_id": intervention_id,
            "student_id": student_id,
            "student_name": student_name,
            "course_id": course_id,
            "mentor_id": assigned_mentor["mentor_id"],
            "mentor_name": assigned_mentor["display_name"],
            "status": "offered",  # 'offered', 'accepted', 'declined'
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.mentor_invitations[inv_id] = invitation

        # Send notification to student
        try:
            NotificationService.emit_notification(
                user_id=student_id,
                title="Academic Peer Mentorship Available",
                message=f"A voluntary peer mentor ({assigned_mentor['display_name']}) is available to help with {course_id}. Would you like to connect?",
                category="peer_mentor_offer",
                reference_type="mentor_invitation",
                reference_id=inv_id,
            )
        except Exception:
            pass

        return invitation

    def _create_counselling_offer(
        self, student_id: str, student_name: str, intervention_id: str
    ) -> Dict[str, Any]:
        """Create private non-stigmatizing counselling offer."""
        offer_id = f"coff-{uuid.uuid4().hex[:8]}"
        offer = {
            "offer_id": offer_id,
            "intervention_id": intervention_id,
            "student_id": student_id,
            "student_name": student_name,
            "status": "offered",  # 'offered', 'accepted', 'declined'
            "counsellor_id": "counsellor-meera",
            "counsellor_name": "Dr. Meera Nambiar",
            "counsellor_title": "Campus Wellbeing & Academic Counsellor",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.counselling_offers[offer_id] = offer

        # Send private notification to student
        try:
            NotificationService.emit_notification(
                user_id=student_id,
                title="Confidential Wellbeing Check-In Available",
                message="We noticed academic pressure might be elevated. Confidential support is available with Dr. Meera Nambiar whenever you are ready.",
                category="counselling_offer",
                reference_type="counselling_offer",
                reference_id=offer_id,
            )
        except Exception:
            pass

        return offer

    def _notify_faculty_review(
        self, student_name: str, course_id: str, feed_status: str, acad_status: str
    ):
        """Notify faculty if classroom delivery or academic gaps require review."""
        try:
            NotificationService.emit_notification(
                user_id="user-faculty-1",
                title=f"Faculty Review Flagged for {course_id}",
                message=f"Student Pulse identified a need for instructional review in {course_id} (Feedback: {feed_status}, Academics: {acad_status}).",
                category="faculty_review",
                reference_type="course",
                reference_id=course_id,
            )
        except Exception:
            pass

    def respond_to_mentor_invitation(self, invitation_id: str, accept: bool) -> Dict[str, Any]:
        inv = self.mentor_invitations.get(invitation_id)
        if not inv:
            raise ValueError("Mentor invitation not found.")
        inv["status"] = "accepted" if accept else "declined"
        inv["responded_at"] = datetime.now(timezone.utc).isoformat()

        if accept:
            # Increment mentor active count
            for m in self.peer_mentor_pool:
                if m["mentor_id"] == inv["mentor_id"]:
                    m["active_mentees"] += 1
        return inv

    def respond_to_counselling_offer(self, offer_id: str, accept: bool) -> Dict[str, Any]:
        off = self.counselling_offers.get(offer_id)
        if not off:
            raise ValueError("Counselling offer not found.")
        off["status"] = "accepted" if accept else "declined"
        off["responded_at"] = datetime.now(timezone.utc).isoformat()
        return off

    def list_interventions(self) -> List[Dict[str, Any]]:
        return list(self.interventions_history)

    def list_peer_mentors(self) -> List[Dict[str, Any]]:
        return list(self.peer_mentor_pool)


# Singleton instance
intervention_engine = InterventionEngine()
