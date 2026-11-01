"""DISHA Student Pulse — Intervention Engine.

Implements:
1. Category score normalization (0 to 100) for Academic, Feedback, and Wellbeing.
2. Threshold-based classification (Default: 60.0% threshold, v1.0-operational).
3. The 8-row deterministic intervention matrix:
   - Low Academic -> Peer Mentor Invitation (voluntary matching, privacy preserved)
   - Low Feedback -> Faculty Review (aggregated feedback alerts)
   - Low Wellbeing -> Counsellor Support Offer (private, student-empowered consent)
4. Peer Mentor Pool matching and invitation lifecycle.
5. Counsellor private support offer lifecycle.
6. Deduplication and historical audit logging.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.modules.pulse.question_bank import COURSE_QUESTION_BANK
from app.services.notification_service import NotificationService


class PulseInterventionEngine:
    DEFAULT_THRESHOLD = 60.0
    VERSION = "v1.0-operational"

    def __init__(self):
        self.question_bank_map = {q["id"]: q for q in COURSE_QUESTION_BANK}
        # In-memory stores backing the relational entities
        self.peer_mentor_pool: Dict[str, Dict[str, Any]] = {}
        self.mentor_requests: Dict[str, Dict[str, Any]] = {}
        self.counsellor_offers: Dict[str, Dict[str, Any]] = {}
        self.intervention_records: List[Dict[str, Any]] = []
        self.threshold_configs: Dict[str, float] = {
            "ACADEMIC": self.DEFAULT_THRESHOLD,
            "CLASSROOM_FEEDBACK": self.DEFAULT_THRESHOLD,
            "WELLBEING": self.DEFAULT_THRESHOLD,
        }

        # Seed initial volunteer peer mentors and counsellors
        self._seed_mentor_pool()

    def _seed_mentor_pool(self):
        """Seed high-performing volunteer students eligible to mentor courses."""
        demo_mentors = [
            {
                "id": "mentor-01",
                "student_id": "student-mentor-arjun",
                "student_name": "Arjun Singh",
                "eligible_courses": ["CS201", "CS202"],
                "gpa": 9.2,
                "availability": "AVAILABLE",
                "max_capacity": 3,
                "active_mentees_count": 1,
                "volunteer_status": "ACTIVE_VOLUNTEER",
                "created_at": "2026-10-01T08:00:00Z"
            },
            {
                "id": "mentor-02",
                "student_id": "student-mentor-kavya",
                "student_name": "Kavya Iyer",
                "eligible_courses": ["CS201"],
                "gpa": 8.9,
                "availability": "AVAILABLE",
                "max_capacity": 2,
                "active_mentees_count": 0,
                "volunteer_status": "ACTIVE_VOLUNTEER",
                "created_at": "2026-10-05T09:00:00Z"
            },
            {
                "id": "mentor-03",
                "student_id": "student-mentor-rohan",
                "student_name": "Rohan Verma",
                "eligible_courses": ["CS202"],
                "gpa": 9.0,
                "availability": "AVAILABLE",
                "max_capacity": 3,
                "active_mentees_count": 0,
                "volunteer_status": "ACTIVE_VOLUNTEER",
                "created_at": "2026-10-08T11:00:00Z"
            }
        ]
        for m in demo_mentors:
            mentor_id = str(m["id"])
            self.peer_mentor_pool[mentor_id] = m

    # =========================================================================
    # 1. SCORING & NORMALIZATION (0 TO 100)
    # =========================================================================

    def calculate_academic_score(
        self,
        question_ids: List[str],
        academic_answers: Dict[str, Any]
    ) -> Tuple[float, float, float]:
        """
        Calculate academic score: (Marks Obtained / Total Marks) * 100.
        Returns: (earned_marks, max_marks, normalized_percentage)
        """
        earned = 0.0
        max_marks = 0.0

        for qid in question_ids:
            q = self.question_bank_map.get(qid)
            if not q or q.get("category") != "ACADEMIC":
                continue

            q_max = float(q.get("marks", 2.0))
            max_marks += q_max
            user_ans = academic_answers.get(qid)

            if q.get("question_type") == "mcq":
                correct_idx = q.get("correct_option")
                if user_ans is not None and str(user_ans).strip() != "":
                    try:
                        if int(user_ans) == correct_idx:
                            earned += q_max
                    except (ValueError, TypeError):
                        pass
            elif q.get("question_type") == "descriptive":
                # Provisional rubric score (80% default pending faculty manual rubric mark)
                if user_ans and len(str(user_ans).strip()) >= 10:
                    earned += q_max * 0.8

        pct = round((earned / max_marks) * 100, 1) if max_marks > 0 else 0.0
        return round(earned, 1), round(max_marks, 1), pct

    def calculate_feedback_score(
        self,
        question_ids: List[str],
        feedback_answers: Dict[str, Any]
    ) -> Optional[float]:
        """
        Calculate positive-direction normalized feedback score (0 to 100).
        Likert: 1=0, 2=25, 3=50, 4=75, 5=100.
        Pace: Just right = 100, Too fast = 40, Too slow = 50.
        Excludes optional descriptive comments from numerical score.
        """
        scores = []
        for qid in question_ids:
            q = self.question_bank_map.get(qid)
            if not q or q.get("category") != "CLASSROOM_FEEDBACK":
                continue

            # Skip descriptive questions from numerical scoring
            if q.get("question_type") == "descriptive":
                continue

            ans = feedback_answers.get(qid)
            if ans is None or str(ans).strip() == "":
                continue

            if q.get("question_type") == "likert":
                # Convert 1-5 scale or integer index to 0-100
                try:
                    val = int(ans)
                    if 1 <= val <= 5:
                        scores.append((val - 1) * 25.0)
                    elif 0 <= val <= 4:
                        scores.append(val * 25.0)
                except (ValueError, TypeError):
                    pass
            elif q.get("question_type") == "single_choice":
                ans_str = str(ans).lower()
                if "just right" in ans_str or "very engaged" in ans_str or "extremely helpful" in ans_str or "always" in ans_str or "very clear" in ans_str:
                    scores.append(100.0)
                elif "somewhat" in ans_str or "moderately" in ans_str or "occasionally" in ans_str or "usually" in ans_str:
                    scores.append(60.0)
                elif "too fast" in ans_str or "too slow" in ans_str or "rarely" in ans_str or "not very" in ans_str or "frequently" in ans_str:
                    scores.append(35.0)
                elif "uncomfortable" in ans_str or "unclear" in ans_str or "hesitant" in ans_str:
                    scores.append(20.0)
                else:
                    scores.append(50.0)

        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    def calculate_wellbeing_score(
        self,
        question_ids: List[str],
        wellbeing_answers: Dict[str, Any]
    ) -> Optional[float]:
        """
        Calculate positively oriented normalized wellbeing score (0 to 100).
        Reverse-scores negatively worded items (e.g. academic pressure, social isolation, exhaustion).
        Excludes missing answers (does not penalize missing as 0).
        """
        scores = []
        for qid in question_ids:
            q = self.question_bank_map.get(qid)
            if not q or q.get("category") != "WELLBEING":
                continue

            ans = wellbeing_answers.get(qid)
            if ans is None or str(ans).strip() == "":
                continue

            param = q.get("parameter_tag", "")
            is_negative_item = param in [
                "academic_pressure",
                "loneliness_frequency",
                "energy_levels",
                "adaptability",
            ]

            if q.get("question_type") == "likert":
                try:
                    val = int(ans)
                    normalized = (val - 1) * 25.0 if 1 <= val <= 5 else val * 25.0
                    normalized = max(0.0, min(100.0, normalized))
                    if is_negative_item:
                        normalized = 100.0 - normalized
                    scores.append(normalized)
                except (ValueError, TypeError):
                    pass
            elif q.get("question_type") == "single_choice":
                ans_str = str(ans).lower()
                if is_negative_item:
                    # Negative item: High overwhelm/isolation = Low wellbeing
                    if "almost constantly" in ans_str or "almost daily" in ans_str or "every day" in ans_str:
                        scores.append(15.0)
                    elif "frequently" in ans_str or "several days" in ans_str or "a few times" in ans_str:
                        scores.append(35.0)
                    elif "occasionally" in ans_str or "once or twice" in ans_str:
                        scores.append(65.0)
                    elif "rarely" in ans_str or "never" in ans_str:
                        scores.append(95.0)
                    else:
                        scores.append(50.0)
                else:
                    # Positive item: High connection/resilience = High wellbeing
                    if "yes" in ans_str or "supportive" in ans_str or "persist" in ans_str or "effectively" in ans_str or "great study" in ans_str or "fully" in ans_str:
                        scores.append(100.0)
                    elif "somewhat" in ans_str or "fairly" in ans_str or "moderately" in ans_str:
                        scores.append(60.0)
                    elif "no" in ans_str or "isolated" in ans_str or "give up" in ans_str or "poorly" in ans_str or "struggle" in ans_str:
                        scores.append(25.0)
                    else:
                        scores.append(50.0)

        # Do not score if insufficient data (< 2 valid items answered)
        if len(scores) < 2:
            return None
        return round(sum(scores) / len(scores), 1)

    # =========================================================================
    # 2. THRESHOLD EVALUATION & INTERVENTION MATRIX
    # =========================================================================

    def evaluate_interventions(
        self,
        submission_id: str,
        student_id: str,
        pulse_id: str,
        course_id: str,
        academic_score: float,
        feedback_score: Optional[float],
        wellbeing_score: Optional[float],
    ) -> Dict[str, Any]:
        """
        Evaluate the 8-row intervention matrix against the 60% operational threshold.
        """
        # Threshold checks (>= 60 is GOOD, < 60 is LOW)
        acad_thresh = self.threshold_configs.get("ACADEMIC", self.DEFAULT_THRESHOLD)
        feed_thresh = self.threshold_configs.get("CLASSROOM_FEEDBACK", self.DEFAULT_THRESHOLD)
        well_thresh = self.threshold_configs.get("WELLBEING", self.DEFAULT_THRESHOLD)

        acad_status = "GOOD" if academic_score >= acad_thresh else "LOW"
        feed_status = "GOOD" if (feedback_score is None or feedback_score >= feed_thresh) else "LOW"
        well_status = "GOOD" if (wellbeing_score is None or wellbeing_score >= well_thresh) else "LOW"

        # Apply 8-row decision matrix
        recommended_actions = []
        if acad_status == "LOW" and feed_status == "GOOD" and well_status == "GOOD":
            recommended_actions = ["PEER_MENTOR_INVITATION"]
        elif acad_status == "LOW" and feed_status == "LOW" and well_status == "GOOD":
            recommended_actions = ["PEER_MENTOR_INVITATION", "FACULTY_REVIEW"]
        elif acad_status == "LOW" and feed_status == "GOOD" and well_status == "LOW":
            recommended_actions = ["PEER_MENTOR_INVITATION", "COUNSELLOR_OFFER"]
        elif acad_status == "LOW" and feed_status == "LOW" and well_status == "LOW":
            recommended_actions = ["PEER_MENTOR_INVITATION", "COUNSELLOR_OFFER", "FACULTY_REVIEW"]
        elif acad_status == "GOOD" and feed_status == "LOW" and well_status == "GOOD":
            recommended_actions = ["FACULTY_REVIEW"]
        elif acad_status == "GOOD" and feed_status == "GOOD" and well_status == "LOW":
            recommended_actions = ["COUNSELLOR_OFFER"]
        elif acad_status == "GOOD" and feed_status == "LOW" and well_status == "LOW":
            recommended_actions = ["COUNSELLOR_OFFER", "FACULTY_REVIEW"]
        else: # GOOD, GOOD, GOOD
            recommended_actions = []

        # Deduplication check: prevent multiple duplicate open interventions for same student & course
        existing = next(
            (
                r for r in self.intervention_records
                if r["student_id"] == student_id and r["course_id"] == course_id and r["status"] == "GENERATED"
            ),
            None
        )

        record_id = f"intv-{uuid.uuid4().hex[:8]}"
        record = {
            "id": record_id,
            "submission_id": submission_id,
            "student_id": student_id,
            "pulse_id": pulse_id,
            "course_id": course_id,
            "academic_score": academic_score,
            "feedback_score": feedback_score if feedback_score is not None else 100.0,
            "wellbeing_score": wellbeing_score if wellbeing_score is not None else 100.0,
            "academic_status": acad_status,
            "feedback_status": feed_status,
            "wellbeing_status": well_status,
            "recommended_actions": recommended_actions,
            "status": "GENERATED",
            "scoring_version": self.VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if not existing:
            self.intervention_records.append(record)

        # Execute recommended actions
        triggered_actions = {}
        if "PEER_MENTOR_INVITATION" in recommended_actions:
            triggered_actions["peer_mentor"] = self._trigger_peer_mentor_invitation(
                submission_id=submission_id,
                student_id=student_id,
                course_id=course_id
            )

        if "COUNSELLOR_OFFER" in recommended_actions:
            triggered_actions["counsellor_offer"] = self._trigger_counsellor_offer(
                submission_id=submission_id,
                student_id=student_id
            )

        if "FACULTY_REVIEW" in recommended_actions:
            triggered_actions["faculty_review"] = self._trigger_faculty_review(
                pulse_id=pulse_id,
                course_id=course_id,
                feed_status=feed_status,
                acad_status=acad_status
            )

        return {
            "intervention_record": record,
            "academic_status": acad_status,
            "feedback_status": feed_status,
            "wellbeing_status": well_status,
            "recommended_actions": recommended_actions,
            "triggered_actions": triggered_actions
        }

    # =========================================================================
    # 3. ACTION WORKFLOWS (MENTOR POOL, COUNSELLOR OFFER, FACULTY REVIEW)
    # =========================================================================

    def _trigger_peer_mentor_invitation(
        self,
        submission_id: str,
        student_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """Find an eligible, available peer mentor and emit a voluntary invitation."""
        available_mentors = [
            m for m in self.peer_mentor_pool.values()
            if course_id in m.get("eligible_courses", [])
            and m.get("availability") == "AVAILABLE"
            and m.get("active_mentees_count", 0) < m.get("max_capacity", 3)
            and m.get("student_id") != student_id
        ]

        if not available_mentors:
            return {
                "status": "WAITLISTED",
                "message": "No peer mentors currently available for this subject; added to coordinator matching queue."
            }

        # Select mentor with lowest active load
        available_mentors.sort(key=lambda m: m.get("active_mentees_count", 0))
        mentor = available_mentors[0]

        req_id = f"req-mentor-{uuid.uuid4().hex[:6]}"
        request_obj = {
            "id": req_id,
            "submission_id": submission_id,
            "student_id": student_id,
            "mentor_id": mentor["student_id"],
            "mentor_name": mentor["student_name"],
            "course_id": course_id,
            "status": "OFFERED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "responded_at": None,
        }
        self.mentor_requests[req_id] = request_obj

        # Send notification to the peer mentor
        NotificationService.emit_notification(
            user_id=mentor["student_id"],
            title="Peer Mentorship Invitation",
            message=f"You have a new peer mentorship invitation for {course_id}. Your academic support can help a fellow classmate excel.",
            category="MENTORSHIP",
            reference_type="mentor_request",
            reference_id=req_id
        )

        return {
            "status": "OFFERED",
            "request_id": req_id,
            "mentor_name": mentor["student_name"],
            "course_id": course_id
        }

    def _trigger_counsellor_offer(
        self,
        submission_id: str,
        student_id: str
    ) -> Dict[str, Any]:
        """Generate a private, confidential counselling offer to the student."""
        offer_id = f"offer-counsel-{uuid.uuid4().hex[:6]}"
        offer_obj = {
            "id": offer_id,
            "submission_id": submission_id,
            "student_id": student_id,
            "counsellor_id": "counsellor-dr-meera",
            "counsellor_name": "Dr. Meera Nambiar (Lead Student Counsellor)",
            "status": "OFFERED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "responded_at": None,
        }
        self.counsellor_offers[offer_id] = offer_obj

        # Private notification delivered exclusively to the student
        NotificationService.emit_notification(
            user_id=student_id,
            title="Confidential Support Available",
            message="We noticed things might feel demanding lately. DISHA offers completely confidential one-on-one sessions with our campus counsellor. You may accept or decline anytime.",
            category="WELLBEING_OFFER",
            reference_type="counsellor_offer",
            reference_id=offer_id
        )

        return {
            "status": "OFFERED",
            "offer_id": offer_id,
            "counsellor_name": offer_obj["counsellor_name"],
            "privacy_notice": "Strictly confidential: Faculty, peers, and mentors cannot view your wellbeing responses."
        }

    def _trigger_faculty_review(
        self,
        pulse_id: str,
        course_id: str,
        feed_status: str,
        acad_status: str
    ) -> Dict[str, Any]:
        """Alert faculty to review instructional pace, explanation clarity, or difficulty."""
        reasons = []
        if feed_status == "LOW":
            reasons.append("Classroom feedback indicators show pace or explanation clarity concerns")
        if acad_status == "LOW":
            reasons.append("Elevated academic difficulty across core concepts")

        message = f"Student Pulse review alert for {course_id}: {'; '.join(reasons)}. Review aggregated feedback in Assignments Analytics."

        NotificationService.emit_notification(
            user_id="prof-sharma",
            title="Faculty Instructional Review Triggered",
            message=message,
            category="ACADEMIC_ALERT",
            reference_type="pulse_assignment",
            reference_id=pulse_id
        )

        return {
            "status": "ALERTED",
            "reasons": reasons,
            "course_id": course_id
        }

    # =========================================================================
    # 4. LIFECYCLE MANAGEMENT (ACCEPT/DECLINE)
    # =========================================================================

    def respond_to_mentor_request(self, request_id: str, accepted: bool) -> Dict[str, Any]:
        """Handle mentor accept or decline; if declined, cascade to another mentor."""
        req = self.mentor_requests.get(request_id)
        if not req:
            raise ValueError("Mentorship request not found.")

        req["responded_at"] = datetime.now(timezone.utc).isoformat()
        if accepted:
            req["status"] = "ACCEPTED"
            # Increment mentor active count
            for m in self.peer_mentor_pool.values():
                if m.get("student_id") == req["mentor_id"]:
                    m["active_mentees_count"] = m.get("active_mentees_count", 0) + 1
                    if m["active_mentees_count"] >= m.get("max_capacity", 3):
                        m["availability"] = "BUSY"

            # Notify the mentee
            NotificationService.emit_notification(
                user_id=req["student_id"],
                title="Peer Mentor Connected!",
                message=f"{req['mentor_name']} has accepted your peer mentorship request for {req['course_id']}. You can now coordinate study sessions in Messages.",
                category="MENTORSHIP",
                reference_type="mentor_request",
                reference_id=request_id
            )
            return {"status": "ACCEPTED", "message": f"Connected with mentee for {req['course_id']}."}
        else:
            req["status"] = "DECLINED"
            # Try cascading to another available mentor
            cascade = self._trigger_peer_mentor_invitation(
                submission_id=req["submission_id"],
                student_id=req["student_id"],
                course_id=req["course_id"]
            )
            return {"status": "DECLINED", "cascade_status": cascade.get("status")}

    def respond_to_counsellor_offer(self, offer_id: str, accepted: bool) -> Dict[str, Any]:
        """Handle student acceptance or decline of counselling support offer."""
        offer = self.counsellor_offers.get(offer_id)
        if not offer:
            raise ValueError("Counselling offer not found.")

        offer["responded_at"] = datetime.now(timezone.utc).isoformat()
        if accepted:
            offer["status"] = "ACCEPTED"
            # Notify counsellor of accepted session
            NotificationService.emit_notification(
                user_id=offer.get("counsellor_id", "counsellor-dr-meera"),
                title="New Student Support Session Accepted",
                message="A student has accepted a confidential wellbeing check-in. Meeting channel initialized.",
                category="COUNSELLOR_SESSION",
                reference_type="counsellor_offer",
                reference_id=offer_id
            )
            return {
                "status": "ACCEPTED",
                "message": "Counsellor session accepted. You can schedule your preferred meeting slot or message Dr. Meera Nambiar."
            }
        else:
            offer["status"] = "DECLINED"
            return {
                "status": "DECLINED",
                "message": "Counselling offer respectfully closed. Remember, support is always available whenever you choose to reach out."
            }


# Singleton engine instance
pulse_intervention_engine = PulseInterventionEngine()

