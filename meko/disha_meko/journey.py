"""A student's complete academic journey in Meko: one conversation per student, one turn per academic event.

Exact marks live in the ERP / canonical Postgres tables. Meko holds the narrative: short readable sentences
that Meko turns into durable memories ("scored 48% on TMA3, below the class median, risk rose to HIGH").

Event types (metadata.event_type): admission_baseline, assessment_update, tier_change, drift_event,
term_summary, case_event, intervention, outcome, mentor_note.

Each event has a pure builder (`*_turn`, returns a turn dict) and an async function (`await admission_baseline(client, ...)`)
that posts it. Read side: journey_timeline, journey_briefing, correct_memory, forget_memory (the backend exposes these).
Students are always hashed (needs MEKO_PII_SALT); every text passes the PII guard; no mark tables, no counselling notes.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

from . import guard

EVENT_TYPES = ("admission_baseline", "assessment_update", "tier_change", "drift_event", "term_summary",
               "case_event", "intervention", "outcome", "mentor_note")
NOTE_MAX = 400
TIER_WORDS = {"HIGH": "high risk", "MEDIUM": "medium risk", "WATCH": "on watch", "ON_TRACK": "on track"}


def _pct(v: Any) -> str:
    return "n/a" if v is None else f"{float(v):.0f}%"


def _ordinal(n: float) -> str:
    n = int(round(n))
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _meta(event: str, **kw) -> dict:
    return {"event_type": event, **{k: v for k, v in kw.items() if v is not None}}


def _turn(student, event, input_, output, reasoning, meta, key="") -> dict:
    """Seed is deterministic so re-running the same snapshot cannot duplicate a turn."""
    seed = "journey:" + hashlib.sha256(f"{student}|{event}|{key}".encode()).hexdigest()[:24]
    return {"student": student, "input": input_, "output": output, "reasoning": reasoning,
            "metadata": meta, "seed": seed}


def _tier_words(t: Any) -> str:
    return TIER_WORDS.get(str(t), str(t).lower())


# ---- builders --------------------------------------------------------------------------
def admission_baseline_turn(student, *, programme, level=None, tenth_pct=None, twelfth_pct=None,
                            entrance_pct=None, year=None) -> dict:
    marks = [(n, v) for n, v in (("10th", tenth_pct), ("12th", twelfth_pct), ("entrance", entrance_pct)) if v is not None]
    given = ", ".join(f"{n} {_pct(v)}" for n, v in marks) or "no entry percentages on record"
    avg = sum(v for _, v in marks) / len(marks) if marks else None
    band = "no entry baseline" if avg is None else "strong" if avg >= 75 else "average" if avg >= 55 else "below-average"
    return _turn(student, "admission_baseline",
                 f"A new student joined {programme}{f' ({level})' if level else ''}"
                 f"{f', year {year}' if year else ''}. Entry percentages: {given}.",
                 f"Admission baseline recorded: {band} entry profile"
                 f"{f' (average {avg:.0f}% across {len(marks)} entry measures)' if avg is not None else ''}.",
                 "The entry profile is the baseline later performance is compared against, so a drop below it is flagged early.",
                 _meta("admission_baseline", programme=programme, level=level, year=year), "admission")


def assessment_update_turn(student, *, course, term, day, assessment, score_pct=None, class_median=None,
                           standing_pct=None, missed=False, late=False, mean_pct=None, risk=None, tier=None,
                           previous_tier=None, reasons: Iterable[str] = ()) -> dict:
    """One sentence about the assessment (score and class standing, or missed/late) plus DISHA's assessment."""
    where = f"{assessment} in {course} ({term}, day {day})"
    if missed:
        what = f"The student missed {where}."
    else:
        what = f"The student scored {_pct(score_pct)} on {where}"
        if class_median is not None:
            gap = (score_pct or 0) - class_median
            what += (f", {abs(gap):.0f} points {'above' if gap >= 0 else 'below'} the class median of {_pct(class_median)}"
                     if abs(gap) >= 1 else f", in line with the class median of {_pct(class_median)}")
        if standing_pct is not None:
            what += f", {_ordinal(standing_pct)} percentile in the class"
        what += " and submitted late." if late else "."
    reasons = [r for r in reasons if r][:3]
    tier_txt = _tier_words(tier) if tier else "unscored"
    moved = f", moved from {_tier_words(previous_tier)}" if previous_tier and previous_tier != tier else ""
    out = f"DISHA risk {_pct(None if risk is None else risk * 100)} ({tier_txt}{moved})" + \
          (f"; top reasons: {'; '.join(reasons)}." if reasons else ".")
    return _turn(student, "assessment_update", what, out,
                 f"Assessment update after {assessment}: " + ("; ".join(reasons) if reasons else "no risk reasons flagged")
                 + (f". Running mean {_pct(mean_pct)}." if mean_pct is not None else "."),
                 _meta("assessment_update", course=course, term=term, day=day, assessment_id=assessment, tier=tier,
                       risk=None if risk is None else round(float(risk), 3), missed=bool(missed) or None, late=bool(late) or None),
                 f"{course}|{term}|{assessment}|{day}")


def tier_change_turn(student, *, course, term, day, assessment, previous_tier, tier, risk=None, reasons=()) -> dict:
    better = ["HIGH", "MEDIUM", "WATCH", "ON_TRACK"].index(tier) > ["HIGH", "MEDIUM", "WATCH", "ON_TRACK"].index(previous_tier) \
        if tier in TIER_WORDS and previous_tier in TIER_WORDS else None
    verb = "improved" if better else "worsened" if better is False else "changed"
    reasons = [r for r in reasons if r][:3]
    return _turn(student, "tier_change",
                 f"After {assessment} in {course} ({term}, day {day}) the student's risk tier {verb} from "
                 f"{_tier_words(previous_tier)} to {_tier_words(tier)}.",
                 f"Tier change {previous_tier} to {tier}" + (f" at risk {_pct(float(risk) * 100)}" if risk is not None else "")
                 + (f"; main reasons: {'; '.join(reasons)}." if reasons else "."),
                 "The tier moved because the risk score crossed a calibrated cutoff after the latest marks and engagement.",
                 _meta("tier_change", course=course, term=term, day=day, assessment_id=assessment, tier=tier,
                       previous_tier=previous_tier, risk=None if risk is None else round(float(risk), 3)),
                 f"{course}|{term}|{day}|{previous_tier}>{tier}")


def drift_event_turn(student, *, course, term, day, assessment, code, text, tier=None, risk=None) -> dict:
    return _turn(student, "drift_event",
                 f"Early-warning event in {course} ({term}, day {day}): {text}.",
                 f"Drift event {code}" + (f"; the student is currently {_tier_words(tier)}" if tier else "") + ".",
                 "Sudden changes in marks, submissions or online activity often come before a formal tier change, so they are logged.",
                 _meta("drift_event", course=course, term=term, day=day, assessment_id=assessment, tier=tier,
                       risk=None if risk is None else round(float(risk), 3), code=code),
                 f"{course}|{term}|{day}|{code}")


def _weak_co(w: dict) -> str:
    desc = w.get("description")
    pct, lvl = w.get("pct"), w.get("level")
    return (w["co"] + (f" {desc}" if desc else "") + (f" at {_pct(pct)}" if pct is not None else "")
            + (f" (level {lvl})" if lvl is not None else ""))


def term_summary_turn(student, *, term, courses: list[dict], tier=None) -> dict:
    """courses: [{course, mean_pct, trend ('improving'|'declining'|'steady'), weak_cos: [{co, description?, pct?, level?}]}]"""
    parts = []
    for c in courses:
        s = f"{c['course']} mean {_pct(c.get('mean_pct'))}, {c.get('trend') or 'steady'}"
        weak = [w for w in c.get("weak_cos") or []]
        if weak:
            s += "; weak outcomes: " + ", ".join(_weak_co(w) for w in weak[:3])
        parts.append(s)
    n_weak = sum(len(c.get("weak_cos") or []) for c in courses)
    return _turn(student, "term_summary",
                 f"End of term {term}. Per course: " + "; ".join(parts) + ".",
                 f"Term {term} summary: {len(courses)} course{'s' if len(courses) != 1 else ''}, {n_weak} weak course outcome"
                 f"{'s' if n_weak != 1 else ''}" + (f", ending {_tier_words(tier)}." if tier else "."),
                 "Course means and trends come from the term's assessments; weak outcomes are course outcomes below target.",
                 _meta("term_summary", term=term, tier=tier, n_courses=len(courses)), f"{term}")


def case_event_turn(student, *, case_id, event, tier=None, reason_codes=(), course=None, term=None, day=None, note=None) -> dict:
    codes = ", ".join(sorted(set(reason_codes))) or "no reason codes"
    return _turn(student, "case_event",
                 f"Support case {event}" + (f" for {course}" if course else "") + f" (reasons: {codes})"
                 + (f"; {note}" if note else "") + ".",
                 f"Case {event}" + (f" at {_tier_words(tier)}" if tier else "") + ".",
                 "A staff member acted on a DISHA flag; the case lifecycle is part of the student's story.",
                 _meta("case_event", course=course, term=term, day=day, tier=tier, case=case_id, status=event), f"{case_id}|{event}")


def intervention_turn(student, *, intervention_id, case_id=None, reason_codes=(), tier=None, course=None, term=None, day=None) -> dict:
    codes = ", ".join(sorted(set(reason_codes))) or "no reason codes"
    return _turn(student, "intervention",
                 f"Intervention {intervention_id} started" + (f" in {course}" if course else "") + f" (reasons: {codes}).",
                 f"Intervention {intervention_id} recorded" + (f" for a {_tier_words(tier)} student." if tier else "."),
                 "Interventions are chosen from the campus catalogue to address the flagged reasons.",
                 _meta("intervention", course=course, term=term, day=day, tier=tier, case=case_id, intervention_id=intervention_id),
                 f"{case_id}|{intervention_id}")


def outcome_turn(student, *, outcome, intervention_id, case_id=None, reason_codes=(), tier=None, course=None, term=None, day=None) -> dict:
    codes = ", ".join(sorted(set(reason_codes))) or "no reason codes"
    return _turn(student, "outcome",
                 f"Outcome of intervention {intervention_id}: {outcome.replace('_', ' ')} (reasons: {codes}).",
                 f"Outcome recorded: {outcome.replace('_', ' ')}.",
                 "Outcomes are reviewed by staff after follow-up and feed the playbook of what worked.",
                 _meta("outcome", course=course, term=term, day=day, tier=tier, case=case_id, intervention_id=intervention_id,
                       outcome=outcome), f"{case_id}|{intervention_id}|{outcome}")


def looks_like_table(text: str) -> bool:
    lines = [l for l in text.splitlines() if len(re.findall(r"\d+(?:\.\d+)?", l)) >= 3]
    return len(lines) >= 3 or text.count("|") >= 6 or text.count("\t") >= 6


def mentor_note_turn(student, *, text, course=None, term=None, day=None) -> dict | None:
    """Mentor-written note, PII-stripped (email, phone, id-like tokens; the course code is kept) and capped.
    None when it looks like a mark table. Counselling content belongs in the ERP, not here (see MEKO_INTEGRATION.md)."""
    if looks_like_table(text or ""):
        return None
    keep = {}
    t = text or ""
    for i, tok in enumerate(x for x in (course, term) if x):
        t = t.replace(tok, f"\x00{i}\x00")
        keep[f"\x00{i}\x00"] = tok
    t = guard.strip_pii(" ".join(t.split()))
    for ph, tok in keep.items():
        t = t.replace(ph, tok)
    t = t[:NOTE_MAX].strip()
    if not t:
        return None
    return _turn(student, "mentor_note", f"Mentor note{f' on {course}' if course else ''}: {t}",
                 "Mentor note added to the academic journey.",
                 "Written by the student's mentor; the mentor's context is kept alongside DISHA's assessments.",
                 _meta("mentor_note", course=course, term=term, day=day),
                 hashlib.sha256(t.encode()).hexdigest()[:12])


# ---- posting (one function per event type) -------------------------------------------------
async def _post(client, turn) -> bool:
    return bool(turn) and await client.journey_post([turn]) == 1


async def admission_baseline(client, student, **kw) -> bool:
    return await _post(client, admission_baseline_turn(student, **kw))


async def assessment_update(client, student, **kw) -> bool:
    return await _post(client, assessment_update_turn(student, **kw))


async def tier_change(client, student, **kw) -> bool:
    return await _post(client, tier_change_turn(student, **kw))


async def drift_event(client, student, **kw) -> bool:
    return await _post(client, drift_event_turn(student, **kw))


async def term_summary(client, student, **kw) -> bool:
    return await _post(client, term_summary_turn(student, **kw))


async def case_event(client, student, **kw) -> bool:
    return await _post(client, case_event_turn(student, **kw))


async def intervention(client, student, **kw) -> bool:
    return await _post(client, intervention_turn(student, **kw))


async def outcome(client, student, **kw) -> bool:
    return await _post(client, outcome_turn(student, **kw))


async def mentor_note(client, student, **kw) -> bool:
    return await _post(client, mentor_note_turn(student, **kw))


# ---- reading it back (the backend exposes these) -----------------------------------------------
async def journey_timeline(client, student, limit: int = 100, meko_enabled: bool = True) -> list[dict]:
    """GET /students/{id}/journey: the conversation turns in order, as Meko returned them."""
    return await client.journey_timeline(student, limit) if meko_enabled else []


async def journey_briefing(client, student, question: str | None = None, meko_enabled: bool = True, k: int = 10) -> dict:
    """GET /students/{id}/briefing?meko=on|off: recalled items verbatim {id, source, text}. Off -> empty items."""
    return await client.journey_briefing(student, question, k=k, meko_enabled=meko_enabled)


async def correct_memory(client, memory_id: str, text: str) -> bool:
    """PATCH /meko/memories/{id}"""
    return await client.correct_memory(memory_id, text)


async def forget_memory(client, memory_id: str) -> bool:
    """DELETE /meko/memories/{id}"""
    return await client.forget_memory(memory_id)


async def erase_student(client, student) -> dict:
    """DELETE /students/{id}/meko: the student's journey and every memory extracted from it."""
    return await client.erase_student(student)


# ---- from a rolling-model insights payload ---------------------------------------------------------
def turns_from_insights(payload: dict, max_students: int | None = None) -> list[dict]:
    """Insights payload (dict) -> journey turns: an assessment_update for every student with a scored assessment, plus
    tier_change and drift_event turns. When there are more students than max_students, those with a tier change or
    drift event come first, then the highest risk."""
    def priority(s):
        r = s["risk"]
        moved = r.get("previous_tier") is not None and r["previous_tier"] != r["tier"]
        return (not (moved or s["drift_events"]), -float(r.get("probability") or 0))
    students = sorted(payload.get("students", []), key=priority)
    seen, picked = set(), []
    for s in students:
        if max_students is not None and s["student_id"] not in seen and len(seen) >= max_students:
            continue
        seen.add(s["student_id"])
        picked.append(s)
    turns = []
    for s in picked:
        if not s.get("last_assessment"):
            continue
        r, snap = s["risk"], s.get("snapshot") or {}
        base = dict(course=s["course_id"], term=s["term_id"], day=s["as_of_day"], assessment=s["last_assessment"])
        reasons = [x["text"] for x in s.get("reasons", [])]
        turns.append(assessment_update_turn(
            s["student_id"], **base, score_pct=snap.get("last_score"), class_median=snap.get("class_median_score"),
            standing_pct=snap.get("standing_pct"), missed=bool(snap.get("consecutive_misses")),
            mean_pct=snap.get("mean_score"), risk=r.get("probability"),
            tier=r["tier"], previous_tier=r.get("previous_tier"), reasons=reasons))
        if r.get("previous_tier") is not None and r["previous_tier"] != r["tier"]:
            turns.append(tier_change_turn(s["student_id"], **base, previous_tier=r["previous_tier"], tier=r["tier"],
                                          risk=r.get("probability"), reasons=reasons))
        for e in s.get("drift_events", []):
            turns.append(drift_event_turn(s["student_id"], **base, code=e["code"], text=e["text"],
                                          tier=r["tier"], risk=r.get("probability")))
    return turns
