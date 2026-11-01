"""Seed a believable demo campus into the DISHA database (local Postgres or Supabase).

    python infra/scripts/seed_demo.py            # seed if the demo campus does not exist yet
    python infra/scripts/seed_demo.py --reset    # wipe every disha_* table (except the intervention catalogue) first

Reads DISHA_DATABASE_URL from the environment or the repo-root .env. Run `alembic upgrade head` first.
Everything here is synthetic: invented names, emails on example-style domains, no real student data.

The ML dashboard is real, not painted on: the script writes canonical tables (students, enrolments, assessments,
results, activity), ingests them through the same service as the admin upload, runs the rolling risk model at three
points in the term, and lets the published policy open the cases from the resulting flags.
"""
import argparse
import asyncio
import io
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "ml"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sqlalchemy import select, text, update  # noqa: E402

from app.core.database import AsyncSessionLocal, engine  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.modules.audit.services import AuditService  # noqa: E402
from app.modules.campus.models import Campus  # noqa: E402
from app.modules.cases.models import (  # noqa: E402
    Case, CaseEvent, CaseNote, FollowUp, FollowUpNote, Intervention, InterventionCatalogue, InterventionOutcome,
)
from app.modules.counselling.models import (  # noqa: E402
    CounsellingNote, CounsellingSession, CounsellorAssignment, CounsellorProfile,
)
from app.modules.faculty.models import (  # noqa: E402
    Assessment, AssessmentSubmission, Course, CourseEnrollment, CourseSection, FacultyProfile,
    StudentAttendanceRecord,
)
from app.modules.identity.models import Membership, User  # noqa: E402
from app.modules.ingestion import services as ingest  # noqa: E402
from app.modules.ml.schemas import ScoringRunRequest  # noqa: E402
from app.modules.ml.services import SystemActor, apply_policy_to_run, run_scoring  # noqa: E402
from app.modules.notifications.models import Notification  # noqa: E402
from app.modules.policy.schemas import PolicyDefinition, PolicyVersionCreate  # noqa: E402
from app.modules.policy.services import PolicyService  # noqa: E402
from app.modules.rewards.models import LedgerEntry, RewardItem  # noqa: E402
from app.modules.roster.models import Student  # noqa: E402
from app.modules.student.models import SupportRequest  # noqa: E402
from app.modules.wellbeing.models import PulsePeriod, PulseQuestionnaire, PulseSubmission  # noqa: E402
from app.modules.wellbeing.services import band_of, score_responses  # noqa: E402

CAMPUS_CODE = "DISHA-DEMO"
CAMPUS_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "campus.demo.disha.edu"))
DEMO_PASSWORD = "Demo@12345"
TERM_ID = "2026-T1"
TERM_LENGTH = 120
TERM_DAY_NOW = 77  # the demo "today" sits 77 days into the term
NOW = datetime.now(timezone.utc)
TERM_START = (NOW - timedelta(days=TERM_DAY_NOW)).date()
rng = random.Random(2026)
nprng = np.random.default_rng(2026)

DEPARTMENTS = {
    "Computer Science": ["CS201", "CS230", "CS250", "MA101", "HS102"],
    "Electronics": ["EC210", "CS201", "MA101", "HS102", "EC240"],
    "Mechanical": ["ME205", "MA101", "HS102", "ME230", "EC210"],
    "Business Admin": ["BA220", "BA240", "MA101", "HS102", "BA260"],
}
COURSES = {
    "CS201": ("Data Structures & Algorithms", "Computer Science & IT"),
    "CS230": ("Database Management Systems", "Computer Science & IT"),
    "CS250": ("Operating Systems", "Computer Science & IT"),
    "EC210": ("Signals & Systems", "Engineering"),
    "EC240": ("Digital Electronics", "Engineering"),
    "ME205": ("Engineering Thermodynamics", "Engineering"),
    "ME230": ("Fluid Mechanics", "Engineering"),
    "MA101": ("Engineering Mathematics I", "Mathematics"),
    "HS102": ("Professional Communication", "Humanities"),
    "BA220": ("Marketing Management", "Management"),
    "BA240": ("Financial Accounting", "Management"),
    "BA260": ("Business Analytics", "Management"),
}
FACULTY = [  # (email, name, title, department, courses)
    ("faculty@demo.disha.edu", "Dr. Meera Iyer", "Associate Professor", "Computer Science", ["CS201", "CS230"]),
    ("rohan.kapoor@demo.disha.edu", "Prof. Rohan Kapoor", "Assistant Professor", "Computer Science", ["CS250", "MA101"]),
    ("sunita.rao@demo.disha.edu", "Dr. Sunita Rao", "Professor", "Electronics", ["EC210", "EC240", "HS102"]),
    ("arjun.menon@demo.disha.edu", "Prof. Arjun Menon", "Assistant Professor", "Mechanical", ["ME205", "ME230"]),
    ("kavita.shah@demo.disha.edu", "Dr. Kavita Shah", "Associate Professor", "Business Admin", ["BA220", "BA240", "BA260"]),
]
FIRST = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Ananya", "Diya",
         "Aadhya", "Saanvi", "Myra", "Kiara", "Navya", "Riya", "Pari", "Anika", "Rahul", "Neha", "Karan", "Pooja", "Siddharth",
         "Tanvi", "Rohit", "Sneha", "Manish", "Divya", "Harsh", "Ishita", "Nikhil", "Kavya", "Varun", "Meghna", "Yash", "Tara",
         "Dev", "Simran"]
LAST = ["Sharma", "Verma", "Gupta", "Patel", "Nair", "Reddy", "Iyer", "Singh", "Kulkarni", "Joshi", "Mehta", "Bose", "Das",
        "Banerjee", "Chopra", "Malhotra", "Desai", "Pillai", "Rao", "Khan"]
N_STUDENTS = 84


def uid() -> str:
    return str(uuid.uuid4())


def ago(days: float = 0, hours: float = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours)


def ahead(days: float = 0, hours: float = 0) -> datetime:
    return NOW + timedelta(days=days, hours=hours)


def clip(x, lo=0.0, hi=100.0):
    return float(max(lo, min(hi, x)))


# ---------------------------------------------------------------------------------------------------------------

async def wipe(session) -> None:
    """Remove only the demo campus and its demo users (never other campuses' data)."""
    rows = (await session.execute(text(
        "select table_name from information_schema.columns where table_schema='public' and column_name='campus_id' "
        "and table_name like 'disha\\_%'"))).all()
    pending = [r[0] for r in rows if r[0] != "disha_campuses"]
    # the reward ledger is append-only by trigger; the demo reset is the one sanctioned exception
    await session.execute(text("alter table disha_reward_ledger disable trigger user"))
    pending += ["disha_identity", "disha_campuses"]
    for _ in range(8):  # foreign keys decide the order; retry until every table is clear
        left = []
        for t in pending:
            try:
                async with session.begin_nested():
                    if t == "disha_identity":
                        await session.execute(text("delete from disha_identity where email like '%demo.disha.edu'"))
                    elif t == "disha_campuses":
                        await session.execute(text("delete from disha_campuses where id = :c"), {"c": CAMPUS_ID})
                    else:
                        await session.execute(text(f'delete from "{t}" where campus_id = :c'), {"c": CAMPUS_ID})
            except Exception:
                left.append(t)
        pending = left
        if not pending:
            break
    await session.execute(text("alter table disha_reward_ledger enable trigger user"))
    await session.commit()
    print("  removed previous demo campus" + (f" (could not clear: {pending})" if pending else ""))


def build_people():
    pw_hash = get_password_hash(DEMO_PASSWORD)
    people = {}

    def add(email, name, role, dept=None):
        u = User(id=uid(), email=email, hashed_password=pw_hash, full_name=name, is_active=True, created_at=ago(60))
        m = Membership(id=uid(), user_id=u.id, campus_id=CAMPUS_ID, role=role, department=dept, is_active=True, created_at=ago(60))
        people[email] = (u, m)
        return u

    add("admin@demo.disha.edu", "Anita Deshmukh", "institution_admin", "Administration")
    add("hod@demo.disha.edu", "Dr. Vikram Sethi", "hod", "Computer Science")
    add("counsellor@demo.disha.edu", "Priya Nambiar", "counsellor", "Student Wellbeing")
    add("sana.counsellor@demo.disha.edu", "Sana Qureshi", "counsellor", "Student Wellbeing")
    for email, name, _t, dept, _c in FACULTY:
        add(email, name, "faculty", dept)
    return people


def student_pool():
    """84 students with a latent risk r in [0,1]. ~10% high, ~16% elevated, the rest healthy."""
    names, seen = [], set()
    while len(names) < N_STUDENTS:
        n = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if n not in seen:
            seen.add(n)
            names.append(n)
    depts = list(DEPARTMENTS)
    out = []
    for i, name in enumerate(names):
        r = rng.random()
        latent = rng.uniform(0.72, 0.95) if r < 0.11 else rng.uniform(0.45, 0.7) if r < 0.28 else rng.uniform(0.02, 0.35)
        out.append({
            "uid": f"S26{i + 1:04d}", "name": name, "dept": depts[i % len(depts)], "risk": latent,
            "year": rng.choice([1, 1, 2, 2, 3]), "gender": rng.choice(["F", "M"]),
        })
    # the demo student login is a stressed-but-recoverable student, with an active case
    out[0].update(name="Aarav Sharma", dept="Computer Science", risk=0.82, year=2)
    out[1].update(name="Ananya Iyer", dept="Computer Science", risk=0.2, year=2)
    out[2].update(name="Rahul Verma", dept="Electronics", risk=0.52, year=2)
    out[3].update(name="Kiara Nair", dept="Mechanical", risk=0.12, year=1)
    return out


def canonical_csvs(pool):
    students, enrol, assess, results, activity, withdrawals = [], [], [], [], [], []
    term_start = TERM_START.isoformat()
    due_days = [14, 28, 42, 56, 70]
    weights = [10, 15, 15, 20, 20]
    kinds = ["quiz", "assignment", "midterm", "assignment", "quiz"]
    course_ids = sorted({c for cs in DEPARTMENTS.values() for c in cs})
    for c in course_ids:
        for k, (d, w, kind) in enumerate(zip(due_days, weights, kinds), 1):
            assess.append({"assessment_id": f"{c}-A{k}", "course_id": c, "term_id": TERM_ID, "due_day": d, "weight": w, "type": kind})
    wd_budget = 3
    for s in pool:
        students.append({
            "student_id": s["uid"], "program_level": "ug", "year_of_study": s["year"],
            "tenth_pct": round(clip(88 - 25 * s["risk"] + rng.gauss(0, 4), 45, 99), 1),
            "twelfth_pct": round(clip(86 - 25 * s["risk"] + rng.gauss(0, 4), 45, 99), 1),
            "entrance_pct": round(clip(80 - 30 * s["risk"] + rng.gauss(0, 7), 30, 99), 1),
            "gender": s["gender"],
        })
        for c in DEPARTMENTS[s["dept"]]:
            r = clip(s["risk"] + rng.gauss(0, 0.07), 0, 1)
            enrol.append({"student_id": s["uid"], "term_id": TERM_ID, "course_id": c, "term_length_days": TERM_LENGTH,
                          "term_start": term_start, "credit_load": 4, "prev_attempts": 1 if (r > 0.8 and rng.random() < 0.5) else 0})
            for k, d in enumerate(due_days, 1):
                if d > TERM_DAY_NOW:
                    continue
                # risky students submit less, later and lower, and it worsens as the term goes on
                p_submit = clip(0.98 - 0.75 * r * (0.55 + 0.1 * k), 0.08, 1.0)
                if rng.random() > p_submit:
                    continue
                late = int(abs(rng.gauss(0, 0.6 + 4 * r)))
                score = clip(82 - 48 * r - 3.5 * k * r + rng.gauss(0, 7))
                results.append({"student_id": s["uid"], "assessment_id": f"{c}-A{k}", "submitted_day": d + late, "score_pct": round(score, 1)})
            for day in range(0, TERM_DAY_NOW + 1):
                if day % 7 in (5, 6) and rng.random() < 0.6:
                    continue
                fade = 1 - r * (day / TERM_DAY_NOW) * 0.9
                p_active = clip(0.8 * fade, 0.03, 0.95)
                if rng.random() < p_active:
                    activity.append({"student_id": s["uid"], "course_id": c, "term_id": TERM_ID, "day": day,
                                     "count": max(1, int(nprng.poisson(max(0.5, 9 * fade))))})
            if r > 0.88 and wd_budget > 0 and rng.random() < 0.35:
                wd_budget -= 1
                withdrawals.append({"student_id": s["uid"], "course_id": c, "term_id": TERM_ID, "day": 61})
    return {
        "students": pd.DataFrame(students), "enrolments": pd.DataFrame(enrol), "assessments": pd.DataFrame(assess),
        "results": pd.DataFrame(results), "activity": pd.DataFrame(activity), "withdrawals": pd.DataFrame(withdrawals),
    }


def as_files(frames):
    files = []
    for name, df in frames.items():
        if df.empty:
            continue
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        files.append(ingest.UploadedFile(name, f"{name}.csv", buf.getvalue().encode()))
    return files


# ---------------------------------------------------------------------------------------------------------------

async def seed(reset: bool) -> None:
    async with AsyncSessionLocal() as db:
        exists = (await db.execute(select(Campus.id).where(Campus.code == CAMPUS_CODE))).first()
        if exists and not reset:
            print("Demo campus already exists. Use --reset to rebuild it.")
            return
        if reset:
            await wipe(db)

        print("People and campus")
        db.add(Campus(id=CAMPUS_ID, name="Northfield Institute of Technology", code=CAMPUS_CODE, is_active=True,
                      settings={}, created_at=ago(90)))
        await db.flush()
        people = build_people()
        for u, _m in people.values():
            db.add(u)
        await db.flush()
        for _u, m in people.values():
            db.add(m)
        admin = people["admin@demo.disha.edu"][0]
        counsellors = [people["counsellor@demo.disha.edu"][0], people["sana.counsellor@demo.disha.edu"][0]]
        for c, spec, ph in zip(counsellors, ["Academic stress and exam anxiety", "Adjustment, belonging and family pressure"],
                               ["+91 98200 11001", "+91 98200 11002"]):
            db.add(CounsellorProfile(user_id=c.id, campus_id=CAMPUS_ID, department="Student Wellbeing", specialisation=spec,
                                     designation="Campus Counsellor", phone=ph, availability_status="available"))
        faculty_users = {}
        for email, name, title, dept, courses in FACULTY:
            u = people[email][0]
            faculty_users[email] = (u, courses)
            db.add(FacultyProfile(user_id=u.id, campus_id=CAMPUS_ID, title=title, department=dept,
                                  bio=f"Teaches {', '.join(courses)}."))
        await db.flush()

        print("Courses, sections, roster")
        course_rows, section_rows = {}, {}
        faculty_for_course = {c: u for (u, cs) in faculty_users.values() for c in cs}
        for code, (title, cat) in COURSES.items():
            fac = faculty_for_course[code]
            course = Course(id=uid(), campus_id=CAMPUS_ID, code=code, title=title, category=cat, credits=4,
                            semester="Fall 2026", primary_faculty_id=fac.id)
            section = CourseSection(id=uid(), campus_id=CAMPUS_ID, course_id=course.id, faculty_id=fac.id, section_code="A",
                                    name=f"{code} - Section A", term="Jul - Dec 2026", access_code=f"{code}-{rng.randint(1000, 9999)}",
                                    subject=cat, color=rng.choice(["bg-blue-600", "bg-emerald-600", "bg-violet-600", "bg-amber-600"]))
            course_rows[code], section_rows[code] = course, section
            db.add(course)
        await db.flush()
        for sec in section_rows.values():
            db.add(sec)
        await db.flush()

        pool = student_pool()
        roster = {}
        demo_student_user = User(id=uid(), email="student@demo.disha.edu", hashed_password=get_password_hash(DEMO_PASSWORD),
                                 full_name=pool[0]["name"], is_active=True, created_at=ago(60))
        db.add(demo_student_user)
        extra_logins = {}
        for idx, (mail, who) in enumerate([("ananya.iyer@demo.disha.edu", 1), ("rahul.verma@demo.disha.edu", 2), ("kiara.nair@demo.disha.edu", 3)]):
            u = User(id=uid(), email=mail, hashed_password=get_password_hash(DEMO_PASSWORD), full_name=pool[who]["name"],
                     is_active=True, created_at=ago(60))
            db.add(u)
            extra_logins[who] = u
        await db.flush()
        db.add(Membership(id=uid(), user_id=demo_student_user.id, campus_id=CAMPUS_ID, role="student", department=pool[0]["dept"]))
        for who, u in extra_logins.items():
            db.add(Membership(id=uid(), user_id=u.id, campus_id=CAMPUS_ID, role="student", department=pool[who]["dept"]))
        await db.flush()

        for i, s in enumerate(pool):
            att = clip(96 - 55 * s["risk"] + rng.gauss(0, 4), 35, 100)
            quiz = clip(82 - 50 * s["risk"] + rng.gauss(0, 6), 20, 98)
            user_id = demo_student_user.id if i == 0 else (extra_logins[i].id if i in extra_logins else None)
            email = "student@demo.disha.edu" if i == 0 else (extra_logins[i].email if i in extra_logins else
                    f"{s['name'].lower().replace(' ', '.')}.{s['uid'].lower()}@students.demo.disha.edu")
            st = Student(id=uid(), campus_id=CAMPUS_ID, user_id=user_id, student_uid=s["uid"], full_name=s["name"], email=email,
                         department=s["dept"], course="B.Tech" if s["dept"] != "Business Admin" else "BBA",
                         academic_year=2026 - s["year"] + 1, cohort_code=f"{2026 - s['year'] + 1}-{s['dept'][:3].upper()}",
                         enrollment_status="active", attendance_rate=round(att, 1), quiz_score_avg=round(quiz, 1),
                         is_active=True, created_at=ago(80))
            roster[s["uid"]] = st
            s["row"] = st
            db.add(st)
        await db.flush()

        print("Enrolments, attendance, gradebook")
        today = NOW.date()
        class_days = [today - timedelta(days=d) for d in range(1, 29) if (today - timedelta(days=d)).weekday() < 5][:12]
        for s in pool:
            for code in DEPARTMENTS[s["dept"]]:
                sec = section_rows[code]
                db.add(CourseEnrollment(campus_id=CAMPUS_ID, section_id=sec.id, student_id=s["row"].id, status="enrolled", enrolled_at=ago(75)))
                p_present = clip(0.97 - 0.62 * s["risk"], 0.3, 0.99)
                for d in class_days:
                    status = "present" if rng.random() < p_present else rng.choice(["absent", "absent", "late"])
                    db.add(StudentAttendanceRecord(campus_id=CAMPUS_ID, section_id=sec.id, student_id=s["row"].id, date=d.isoformat(),
                                                   status=status, recorded_by=sec.faculty_id))
        await db.flush()
        assessments = {}
        for code, sec in section_rows.items():
            for k, (title, kind, marks, due) in enumerate([("Quiz 1", "quiz", 20, 14), ("Assignment 1", "assignment", 30, 28),
                                                        ("Midterm", "midterm", 50, 42), ("Assignment 2", "assignment", 30, 56)], 1):
                a = Assessment(id=uid(), campus_id=CAMPUS_ID, section_id=sec.id, title=f"{code} {title}", assessment_type=kind,
                               total_marks=marks, clo_code=f"CLO-{k}", due_at=ago(TERM_DAY_NOW - due), created_by=sec.faculty_id,
                               created_at=ago(TERM_DAY_NOW - due + 7))
                assessments[(code, k)] = a
                db.add(a)
        await db.flush()
        for s in pool:
            for code in DEPARTMENTS[s["dept"]]:
                for k in range(1, 5):
                    a = assessments[(code, k)]
                    if rng.random() > clip(0.98 - 0.5 * s["risk"], 0.3, 1):
                        continue
                    pct = clip(80 - 48 * s["risk"] - 2 * k * s["risk"] + rng.gauss(0, 8))
                    db.add(AssessmentSubmission(campus_id=CAMPUS_ID, assessment_id=a.id, student_id=s["row"].id,
                                                score=round(a.total_marks * pct / 100, 1), graded_by=a.created_by,
                                                feedback=None if pct > 55 else "Please see me during office hours to review this.",
                                                submitted_at=a.due_at))
        await db.commit()

        print("Canonical ML tables -> import -> rolling risk model")
        files = as_files(canonical_csvs(pool))
        batch, dup = await ingest.import_tables(db, campus_id=CAMPUS_ID, actor_id=admin.id, files=files)
        print(f"  import batch {batch.status}, rows={batch.row_counts}, linked={batch.linked_students}")
        if batch.status != "committed":
            print("  validation errors:", batch.validation_errors)
            raise SystemExit(1)
        await db.commit()

        defn = PolicyDefinition.model_validate({
            "tiers": {"high": {"enabled": True, "min_probability": 0.0, "priority": "urgent", "due_in_days": 3},
                      "medium": {"enabled": True, "min_probability": 0.0, "priority": "high", "due_in_days": 7}},
            "cooldown_days": 14, "initial_state": "suggested", "capacity": {"max_new_cases_per_evaluation": 45},
            "reason_rules": [],
        })
        pv = await PolicyService.create_version(db, CAMPUS_ID, admin.id, PolicyVersionCreate(definition=defn, note="Demo campus default policy"))
        await PolicyService.publish_version(db, CAMPUS_ID, admin.id, pv.id)
        await db.commit()

        actor = SystemActor(user_id=admin.id)
        for day in (49, 63, TERM_DAY_NOW):
            run = await run_scoring(db, campus_id=CAMPUS_ID, triggered_by=admin.id, req=ScoringRunRequest(as_of_day=day, term_id=TERM_ID))
            print(f"  scored day {day}: {run.n_scored} rows, tiers {run.tier_counts}")
            if day == TERM_DAY_NOW:
                summary = await apply_policy_to_run(db, run, actor)
                print("  policy:", summary)
        await db.commit()

        print("Case workflow")
        await shape_cases(db, pool, counsellors, admin, faculty_users, course_rows)
        print("Counselling, support requests, pulse, rewards, notifications")
        await seed_counselling(db, pool, counsellors)
        await seed_support_requests(db, pool, faculty_users, course_rows)
        await seed_pulse(db, pool, admin)
        await seed_rewards(db, pool, admin)
        await db.commit()

    async with AsyncSessionLocal() as db:
        counts = {}
        for t in ("disha_roster", "disha_cases", "disha_signals", "disha_ml_scores", "disha_counselling_sessions", "disha_pulse_submissions"):
            counts[t] = (await db.execute(text(f"select count(*) from {t}"))).scalar()
        print("Done.", counts)


async def shape_cases(db, pool, counsellors, admin, faculty_users, course_rows):
    """Spread the cases the policy opened across the workflow, with believable history, and add closed cases."""
    cases = list((await db.execute(select(Case).where(Case.campus_id == CAMPUS_ID).order_by(Case.priority, Case.created_at))).scalars())
    by_uid = {s["row"].id: s for s in pool}
    catalogue = list((await db.execute(select(InterventionCatalogue).order_by(InterventionCatalogue.name))).scalars())
    if not catalogue:
        for name, cat in [("Academic mentoring", "academic"), ("Peer tutoring", "academic"), ("Counselling session", "wellbeing"),
                          ("Attendance contract", "attendance"), ("Financial aid referral", "financial"),
                          ("Study skills workshop", "academic"), ("Family conversation", "wellbeing"), ("Mentor check-in", "academic")]:
            db.add(InterventionCatalogue(id=uid(), campus_id=None, name=name, category=cat, description=name, is_active=True))
        await db.flush()
        catalogue = list((await db.execute(select(InterventionCatalogue).order_by(InterventionCatalogue.name))).scalars())
    catalogue = catalogue[:4]

    # lifecycle plan: (state, hours since opened, has counsellor, intervention progress, followup status)
    # few distinct stages with 5+ cases each, so the privacy small-cell rule does not hide the charts
    plan = ([("suggested", None)] * 6 + [("assigned", "not_started")] * 6
            + [("support_in_progress", "in_progress")] * 8 + [("follow_up_due", "in_progress")] * 6)
    notes_pool = [
        "Spoke with the student after class. They are struggling to balance the workload with a part-time job.",
        "Student acknowledged missing sessions; agreed on a weekly check-in and a catch-up plan for the last two assignments.",
        "Contacted family with the student's consent. Parents were supportive and will help with a fixed study routine.",
        "Attendance has improved from 52% to 68% over the last two weeks. Continue monitoring.",
        "Student reports difficulty with the maths prerequisite. Referred to peer tutoring.",
        "Missed the first scheduled call. Sent a message through the hostel warden; will retry tomorrow.",
        "Discussed time management and exam anxiety. Student is open to a follow-up session next week.",
    ]
    ordered = sorted(cases, key=lambda c: (-({"urgent": 3, "high": 2, "medium": 1, "low": 0}.get(c.priority, 1)), c.created_at))
    # the demo student's case is always an in-progress one the student can see
    demo_case = next((c for c in ordered if by_uid.get(c.student_id, {}).get("uid") == pool[0]["uid"]), None)
    if demo_case:
        ordered.remove(demo_case)
        ordered.insert(11, demo_case)
    for i, case in enumerate(ordered):
        state, progress = plan[i % len(plan)]
        opened = ago(days=rng.uniform(1, 12))
        case.created_at = opened
        c_user = counsellors[i % 2]
        if state in ("suggested", "under_review"):
            case.assigned_counsellor_id = None
        else:
            case.assigned_counsellor_id = c_user.id
        case.status = state
        case.priority = ["urgent", "high", "high", "medium"][i % 4]
        db.add(CaseEvent(case_id=case.id, actor_id=admin.id, campus_id=CAMPUS_ID, event_type="CASE_CREATED",
                         payload={"source": "policy", "priority": case.priority}, created_at=opened))
        if case.assigned_counsellor_id:
            db.add(CaseEvent(case_id=case.id, actor_id=admin.id, campus_id=CAMPUS_ID, event_type="CASE_ASSIGNED",
                             payload={"counsellor_id": c_user.id}, created_at=opened + timedelta(hours=4)))
            db.add(Notification(recipient_id=c_user.id, campus_id=CAMPUS_ID, notification_type="CASE_ASSIGNED", reference_id=case.id,
                                reference_type="case", title="New case assigned", body=f"{case.title}", is_read=rng.random() < 0.5,
                                sent_at=opened, created_at=opened + timedelta(hours=4)))
            db.add(CounsellorAssignment(counsellor_id=c_user.id, student_id=case.student_id, campus_id=CAMPUS_ID, is_active=True,
                                        assigned_at=opened))
        if state not in ("suggested", "under_review"):
            for _ in range(rng.randint(1, 3)):
                db.add(CaseNote(case_id=case.id, author_id=c_user.id, campus_id=CAMPUS_ID, content=rng.choice(notes_pool),
                                created_at=opened + timedelta(days=rng.uniform(0.3, 6))))
            db.add(CaseEvent(case_id=case.id, actor_id=c_user.id, campus_id=CAMPUS_ID, event_type="CASE_STATE_CHANGED",
                             payload={"to": state}, created_at=opened + timedelta(days=1)))
        if progress:
            iv = Intervention(id=uid(), case_id=case.id, catalogue_id=rng.choice(catalogue).id, counsellor_id=c_user.id,
                              campus_id=CAMPUS_ID, description="Agreed support plan with the student.", start_date=opened + timedelta(days=1),
                              target_date=ahead(days=rng.randint(5, 20)), progress=progress, created_at=opened + timedelta(days=1))
            db.add(iv)
            await db.flush()
            if progress == "completed":
                db.add(InterventionOutcome(case_id=case.id, intervention_id=iv.id, counsellor_id=c_user.id, campus_id=CAMPUS_ID,
                                           completion_status=rng.choice(["improved", "improved", "partially_improved"]),
                                           outcome_notes="Attendance and submissions recovered over three weeks.", completed_at=ago(days=1)))
        if state in ("support_in_progress", "follow_up_due", "contact_attempted", "accepted"):
            due_soon = state == "follow_up_due"
            db.add(FollowUp(case_id=case.id, counsellor_id=c_user.id, campus_id=CAMPUS_ID, title="Check-in call with student",
                            description="Review progress on the agreed plan.",
                            scheduled_at=ago(hours=rng.randint(2, 30)) if due_soon else ahead(days=rng.uniform(0.5, 6)),
                            status="scheduled", follow_up_type="follow_up_check"))
        await db.flush()

    # historic closed cases, so the analytics have a month of outcomes behind them
    low_risk = [s for s in pool if s["risk"] < 0.6 and s["uid"] not in {by_uid[c.student_id]["uid"] for c in cases}]
    titles = ["Low attendance - first-year support", "Missed two assessments", "Sudden drop in activity", "Exam anxiety follow-up",
              "Hostel adjustment concern", "Fee-related stress"]
    for j, s in enumerate(low_risk[:14]):
        opened = ago(days=rng.uniform(18, 40))
        c_user = counsellors[j % 2]
        closed_at = opened + timedelta(days=rng.uniform(6, 15))
        case = Case(id=uid(), campus_id=CAMPUS_ID, student_id=s["row"].id, assigned_counsellor_id=c_user.id, status="closed",
                    priority=rng.choice(["medium", "high", "medium"]), title=rng.choice(titles),
                    description="Closed after the agreed support plan was completed.", due_date=opened + timedelta(days=7),
                    closed_at=closed_at, closed_by=c_user.id, created_at=opened, updated_at=closed_at)
        db.add(case)
        await db.flush()
        db.add(CaseEvent(case_id=case.id, actor_id=admin.id, campus_id=CAMPUS_ID, event_type="CASE_CREATED", payload={}, created_at=opened))
        db.add(CaseEvent(case_id=case.id, actor_id=c_user.id, campus_id=CAMPUS_ID, event_type="CASE_CLOSED", payload={}, created_at=closed_at))
        db.add(CaseNote(case_id=case.id, author_id=c_user.id, campus_id=CAMPUS_ID, content=rng.choice(notes_pool), created_at=opened + timedelta(days=2)))
        iv = Intervention(id=uid(), case_id=case.id, catalogue_id=rng.choice(catalogue).id, counsellor_id=c_user.id, campus_id=CAMPUS_ID,
                          description="Support plan completed.", start_date=opened + timedelta(days=1), target_date=closed_at,
                          progress="completed", created_at=opened + timedelta(days=1))
        db.add(iv)
        await db.flush()
        db.add(InterventionOutcome(case_id=case.id, intervention_id=iv.id, counsellor_id=c_user.id, campus_id=CAMPUS_ID,
                                   completion_status=rng.choice(["improved", "improved", "improved", "partially_improved", "no_change"]),
                                   outcome_notes="Student back on track at the next review.", completed_at=closed_at))
        fu = FollowUp(case_id=case.id, counsellor_id=c_user.id, campus_id=CAMPUS_ID, title="Closing review", scheduled_at=closed_at - timedelta(days=1),
                      status="completed", follow_up_type="follow_up_check", contact_status="reached", completed_at=closed_at - timedelta(days=1),
                      completed_by=c_user.id, created_at=opened + timedelta(days=3))
        db.add(fu)
        await db.flush()
        db.add(FollowUpNote(followup_id=fu.id, case_id=case.id, author_id=c_user.id, campus_id=CAMPUS_ID,
                            content="Spoke with the student. Doing well and attending regularly.", created_at=closed_at - timedelta(days=1)))
    await db.flush()
    await AuditService.record_event(db, admin.id, CAMPUS_ID, "campus", CAMPUS_ID, "DEMO_DATA_SEEDED", {"cases": len(cases) + 14})


async def seed_counselling(db, pool, counsellors):
    cases = list((await db.execute(select(Case).where(Case.campus_id == CAMPUS_ID, Case.assigned_counsellor_id.is_not(None),
                                                      Case.status != "closed"))).scalars())
    modes = ["in_person", "video", "in_person", "phone"]
    places = ["Wellbeing Centre, Room 2", "Wellbeing Centre, Room 4", "Block B, Counselling Room"]
    for i, case in enumerate(cases):
        c_id = case.assigned_counsellor_id
        # one completed session in the past with a confidential note
        past = ago(days=rng.uniform(1, 9), hours=rng.randint(0, 6))
        sess = CounsellingSession(id=uid(), campus_id=CAMPUS_ID, student_id=case.student_id, case_id=case.id, counsellor_id=c_id,
                                  scheduled_at=past, duration_minutes=45, mode=rng.choice(modes), location=rng.choice(places),
                                  status="completed", completed_at=past + timedelta(minutes=45), created_by=c_id)
        db.add(sess)
        await db.flush()
        db.add(CounsellingNote(campus_id=CAMPUS_ID, student_id=case.student_id, case_id=case.id, session_id=sess.id, author_id=c_id,
                               content="Student discussed workload pressure and sleep. Agreed small weekly goals; will review at the next session.",
                               created_at=past + timedelta(hours=1)))
        if i % 2 == 0:  # an upcoming one
            when = ahead(days=rng.uniform(0.2, 6), hours=rng.randint(0, 5)).replace(minute=0, second=0, microsecond=0)
            db.add(CounsellingSession(id=uid(), campus_id=CAMPUS_ID, student_id=case.student_id, case_id=case.id, counsellor_id=c_id,
                                      scheduled_at=when, duration_minutes=45, mode=rng.choice(modes), location=rng.choice(places),
                                      status="scheduled", created_by=c_id))
    # a today / tomorrow cluster so the schedule views are not empty
    await db.flush()


async def seed_support_requests(db, pool, faculty_users, course_rows):
    reqs = [
        (0, "CS201", "Academic help", "Thursday 4-5 pm", "I fell behind after missing two weeks. Could we go over the linked list assignment?", "requested"),
        (0, "CS230", "Extension request", "Friday 11 am", "I have a medical certificate for last week and need to talk about the SQL lab deadline.", "accepted"),
        (2, "EC210", "Academic help", "Wednesday 3 pm", "I do not understand Fourier series at all. Can you recommend where to start?", "requested"),
        (4, "CS201", "Mentoring", "Any weekday evening", "I would like a mentor to help plan my semester.", "requested"),
        (5, "ME205", "Academic help", "Monday 2 pm", "Thermo midterm went badly, want to understand where I went wrong.", "completed"),
    ]
    fac_by_course = {c: u for (u, cs) in faculty_users.values() for c in cs}
    for who, code, cat, slot, note, status in reqs:
        db.add(SupportRequest(id=uid(), campus_id=CAMPUS_ID, student_id=pool[who]["row"].id, faculty_id=fac_by_course[code].id,
                              course_id=course_rows[code].id, category=cat, preferred_slot=slot, student_note=note, status=status,
                              faculty_response=("Happy to help. Come to my office hours." if status != "requested" else None),
                              created_at=ago(days=rng.uniform(0.2, 5))))
    await db.flush()


PULSE_QUESTIONS = [
    {"key": "q1", "dimension": "academic_confidence", "text": "I feel confident I can pass my courses this term."},
    {"key": "q2", "dimension": "academic_confidence", "text": "I understand what is being taught in my classes."},
    {"key": "q3", "dimension": "belonging", "text": "I feel I belong in my class and on campus."},
    {"key": "q4", "dimension": "belonging", "text": "I have someone on campus I can talk to when things get hard."},
    {"key": "q5", "dimension": "wellbeing", "text": "I am managing my stress and sleeping well."},
    {"key": "q6", "dimension": "wellbeing", "text": "My workload feels manageable."},
]


async def seed_pulse(db, pool, admin):
    q = PulseQuestionnaire(id=uid(), campus_id=CAMPUS_ID, version_key="v1", questions=PULSE_QUESTIONS, created_by=admin.id, created_at=ago(80))
    db.add(q)
    await db.flush()
    periods = []
    for k in range(5):  # four closed fortnights and the current one
        start = NOW - timedelta(days=14 * (4 - k) + 7)
        p = PulsePeriod(id=uid(), campus_id=CAMPUS_ID, questionnaire_id=q.id, label=f"2026-P{k + 1}", starts_at=start,
                        ends_at=start + timedelta(days=14), created_by=admin.id, created_at=start - timedelta(days=1))
        periods.append(p)
        db.add(p)
    await db.flush()
    for k, p in enumerate(periods):
        current = p.starts_at <= NOW <= p.ends_at
        for s in pool:
            if current and s["uid"] in (pool[0]["uid"],):  # the demo student has not answered yet: they can take it live
                continue
            if rng.random() > (0.55 if current else 0.8):
                continue
            base = 5 - 3.4 * s["risk"] - 0.12 * (k < 3) * s["risk"]  # wellbeing slides with risk and a little over time
            responses = {item["key"]: int(clip(round(base + rng.gauss(0, 0.7)), 1, 5)) for item in PULSE_QUESTIONS}
            dims, index = score_responses(PULSE_QUESTIONS, responses)
            db.add(PulseSubmission(campus_id=CAMPUS_ID, student_id=s["row"].id, period_id=p.id, questionnaire_id=q.id, responses=responses,
                                   dimension_scores=dims, index_score=index, department=s["dept"],
                                   submitted_at=p.starts_at + timedelta(days=rng.uniform(0.2, 6))))
    await db.flush()


async def seed_rewards(db, pool, admin):
    items = [("Library fine waiver", "Campus", 150, 20), ("Cafeteria meal voucher", "Food", 120, 40), ("Priority exam-seat choice", "Academic", 300, 10),
             ("Campus store gift card", "Store", 400, 15), ("Free printing credits (100)", "Campus", 80, 100), ("Guest-lecture front row pass", "Events", 200, 25)]
    for n, cat, cost, stock in items:
        db.add(RewardItem(id=uid(), campus_id=CAMPUS_ID, name=n, category=cat, description=n, cost_points=cost, stock=stock, is_available=True))
    for s in pool:
        pts = int(clip(40 + 160 * (1 - s["risk"]) + rng.gauss(0, 25), 0, 400))
        if pts < 30:
            continue
        for j, (key, amount) in enumerate([("pulse_completed", 20), ("attendance_streak", 30), ("assignment_on_time", 25), ("peer_tutoring", 40)]):
            if sum(a for _k, a in [(key, amount)]) and pts >= 30 * (j + 1):
                db.add(LedgerEntry(campus_id=CAMPUS_ID, student_id=s["row"].id, entry_type="award", activity_key=key,
                                   source_ref=f"seed:{s['uid']}:{key}", points=amount, idempotency_key=f"seed:{s['uid']}:{key}",
                                   created_by=None, note="Seeded demo award", created_at=ago(days=rng.uniform(1, 40))))
    await db.flush()


async def grant_all_roles(email: str) -> None:
    """Make one real account hold every demo role (admin, counsellor, faculty, student) with all their data.

    The demo counsellor, faculty and student personas are folded into the account: every reference to them
    (cases, sessions, sections, roster row, ...) is re-pointed to it, so each role has a full dashboard.
    The audit log is left as written so its hash chain stays valid.
    """
    email = email.lower().strip()
    async with AsyncSessionLocal() as db:
        row = (await db.execute(text("select id from disha_identity where email=:e"), {"e": email})).first()
        if row:
            target = row[0]
        else:
            target = uid()
            await db.execute(text("insert into disha_identity (id,email,hashed_password,full_name,is_active,created_at,updated_at) "
                                  "values (:i,:e,:p,:n,true,now(),now())"),
                             {"i": target, "e": email, "p": get_password_hash(uid()), "n": email.split("@")[0].title()})
        personas = [(r[0], r[1]) for r in await db.execute(text(
            "select id,email from disha_identity where email in ('counsellor@demo.disha.edu','faculty@demo.disha.edu','student@demo.disha.edu')"))]
        cols = [(r[0], r[1]) for r in await db.execute(text(
            "select table_name, column_name from information_schema.columns where table_schema='public' and table_name like 'disha\\_%' "
            "and data_type = 'character varying' and character_maximum_length >= 36 and table_name <> 'disha_audit_events' and not (table_name='disha_identity' and column_name='email')"))]
        # One server-side block per persona: a single round trip instead of hundreds (the database may be far away).
        for old, _mail in personas:
            await db.execute(text("""
                do $$
                declare r record;
                begin
                  for r in select table_name t, column_name c from information_schema.columns
                           where table_schema='public' and table_name like 'disha\\_%'
                             and data_type='character varying' and character_maximum_length >= 36
                             and table_name <> 'disha_audit_events'
                             and not (table_name='disha_identity')
                  loop
                    execute format('update %I set %I = %L where %I = %L', r.t, r.c, '""" + target + """', r.c, '""" + old + """');
                  end loop;
                  delete from disha_identity where id = '""" + old + """';
                end $$;
            """))
        for role in ("institution_admin", "counsellor", "faculty", "student"):  # make sure every role exists, admin included
            await db.execute(text("insert into disha_memberships (id,user_id,campus_id,role,department,is_active,created_at) "
                                  "select cast(:m as varchar),cast(:u as varchar),cast(:c as varchar),cast(:r as varchar),'Demo',true,now() where not exists "
                                  "(select 1 from disha_memberships where user_id=cast(:u as varchar) and campus_id=cast(:c as varchar) and role=cast(:r as varchar))"),
                             {"m": uid(), "u": target, "c": CAMPUS_ID, "r": role})
        await db.execute(text("update disha_identity set full_name=full_name where id=:i"), {"i": target})
        await db.commit()
        roles = [r[0] for r in await db.execute(text("select role from disha_memberships where user_id=:i and is_active"), {"i": target})]
        print(f"{email} now holds: {sorted(set(roles))}")
    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grant-all", metavar="EMAIL", help="after seeding, let this Google account hold every demo role")
    ap.add_argument("--grant-only", metavar="EMAIL", help="skip seeding; just give this account every demo role")
    ap.add_argument("--reset", action="store_true", help="truncate all disha_* tables (keeps the intervention catalogue)")
    args = ap.parse_args()
    async def _main():
        if not args.grant_only:
            await seed(args.reset)
        if args.grant_only or args.grant_all:
            await grant_all_roles(args.grant_only or args.grant_all)
        await engine.dispose()
    asyncio.run(_main())
