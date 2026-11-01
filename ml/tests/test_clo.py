"""CLO insights: hand cases for the math, planted patterns in the synthetic course, privacy, Meko hooks."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from disha_ml import meko_hooks
from disha_ml.clo.analyze import analyze_course, gap_type, level_for, student_co_features
from disha_ml.clo.config import CloConfig
from disha_ml.clo.link import add_co_reasons
from disha_ml.clo.synthetic import COURSE, TERM, make_tables
from disha_ml.rolling.schema import validate
from .rolling_fixtures import tiny_tables

SMALL = CloConfig(min_group_size=1)


def hand(marks, mcq=None, sections=None, max_marks=10, asm_type="Internal"):
    """Tables for one course-term: `marks` = {question_id: [marks per student]}; `mcq` = {qid: (correct, [selected...])}."""
    n = len(next(iter(marks.values())))
    ids = [f"s{i + 1}" for i in range(n)]
    qs = [(q, "A1", "CO1", max_marks, "descriptive", None) for q in marks]
    res = [(sid, q, m, None) for q, v in marks.items() for sid, m in zip(ids, v)]
    for q, (correct, sel) in (mcq or {}).items():
        qs.append((q, "A1", "CO1", 1, "mcq", correct))
        res += [(sid, q, 1.0 if o == correct else 0.0, o) for sid, o in zip(ids, sel)]
    return validate({
        "enrolments": pd.DataFrame({"student_id": ids, "term_id": "T", "course_id": "C", "term_length_days": 100,
                                    "section": sections or ["A"] * n}),
        "assessments": pd.DataFrame({"assessment_id": ["A1"], "course_id": "C", "term_id": "T", "due_day": 10,
                                     "type": asm_type}),
        "questions": pd.DataFrame(qs, columns=["question_id", "assessment_id", "co_id", "max_marks", "type", "correct_option"]),
        "question_results": pd.DataFrame(res, columns=["student_id", "question_id", "marks", "selected_option"]),
    })


# ---- attainment and levels ------------------------------------------------------
def test_level_boundaries():
    assert [level_for(x) for x in (70, 69.9, 60, 59.9, 50, 49.9, 0)] == [3, 2, 2, 1, 1, 0, 0]


def test_attainment_counts_students_at_or_above_target():
    # 10 students, 7 score 60% (== target) and 3 score 50%: 70% attain -> level 3
    p = analyze_course(hand({"Q1": [6] * 7 + [5] * 3}), "C", "T", SMALL, recall=False)
    co = p.co_attainment[0]
    assert (co.attainment_pct, co.level, co.target_pct) == (70.0, 3, 60.0)
    p = analyze_course(hand({"Q1": [6] * 6 + [5] * 4}), "C", "T", SMALL, recall=False)
    assert (p.co_attainment[0].attainment_pct, p.co_attainment[0].level) == (60.0, 2)


def test_internal_and_end_sem_weighted_0_4_0_6():
    t = hand({"Q1": [10] * 10})
    t["assessments"] = pd.concat([t["assessments"], pd.DataFrame({"assessment_id": ["A2"], "course_id": "C", "term_id": "T",
                                                                  "due_day": 90, "type": "Exam"})], ignore_index=True)
    t["questions"] = pd.concat([t["questions"], pd.DataFrame({"question_id": ["Q2"], "assessment_id": ["A2"], "co_id": ["CO1"],
                                                              "max_marks": [10.0], "type": ["descriptive"]})], ignore_index=True)
    t["question_results"] = pd.concat([t["question_results"], pd.DataFrame(
        {"student_id": [f"s{i}" for i in range(1, 11)], "question_id": "Q2", "marks": [0.0] * 10})], ignore_index=True)
    f = student_co_features(t, "C", "T", SMALL)
    assert f["weakest_co_pct"].iloc[0] == 40.0          # 0.4 * 100 + 0.6 * 0


# ---- item analysis -----------------------------------------------------------------
def test_difficulty_and_discrimination_hand_case():
    # 10 students -> top / bottom 27% = 3 students each. Totals: s1..s10 descending.
    q1, q2 = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1], [10, 10, 9, 8, 7, 6, 5, 4, 3, 2]
    p = analyze_course(hand({"Q1": q1, "Q2": q2}), "C", "T", SMALL, recall=False)
    i = {x.question_id: x for x in p.items}
    assert i["Q1"].difficulty_p == 0.55 and i["Q1"].p_top == 0.9 and i["Q1"].p_bottom == 0.2
    assert i["Q1"].discrimination == 0.7
    assert i["Q2"].discrimination == pytest.approx(0.667, abs=1e-3)


def test_negative_discrimination_is_flagged():
    q = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    other = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    p = analyze_course(hand({"Q1": q, "Q2": other, "Q3": other}), "C", "T", SMALL, recall=False)
    q1 = next(x for x in p.items if x.question_id == "Q1")
    assert q1.discrimination < 0 and q1.flag == "negative_discrimination"


# ---- gap type ------------------------------------------------------------------------
def test_gap_classification_rules():
    c = CloConfig()
    assert gap_type(0.49, 0.2, c) == "teaching_gap"
    assert gap_type(0.5, 0.2, c) == "ok"               # top group not strong enough for a student gap
    assert gap_type(0.7, 0.39, c) == "student_gap"
    assert gap_type(0.7, 0.4, c) == "ok"
    assert gap_type(None, None, c) == "insufficient_data"


# ---- misconceptions ----------------------------------------------------------------------
def test_misconception_detection():
    sel = list("BBBBAAACCD")                            # 40% chose B, correct is A
    calm = list("AAAAAAABCD")                           # most common wrong option is 10%
    p = analyze_course(hand({"Q1": [5] * 10}, mcq={"M1": ("A", sel), "M2": ("A", calm)}), "C", "T", SMALL, recall=False)
    m = {x.question_id: x for x in p.misconceptions}
    assert (m["M1"].option, m["M1"].share_pct, m["M1"].flagged) == ("B", 40.0, True)
    assert m["M2"].flagged is False and m["M2"].share_pct == 10.0
    assert any(r.code == "MISCONCEPTION" and "40% chose option B" in r.text for r in p.recommendations)


# ---- privacy ---------------------------------------------------------------------------------
def test_small_class_is_suppressed():
    p = analyze_course(hand({"Q1": [5, 6, 7, 8]}), "C", "T", recall=False)    # default min_group_size = 5
    assert p.co_attainment == [] and p.items == [] and "suppressed" in p.suppressed["note"]


@pytest.fixture(scope="module")
def demo():
    t = make_tables()
    return t, analyze_course(t, COURSE, TERM, recall=False)


def test_small_groups_hidden_in_muddiest_and_sections(demo):
    t, p = demo
    assert {m.key for m in p.muddiest["items"]} == {"CO3", "CO4", "base cases"}   # CO5 had 2 students
    assert p.muddiest["suppressed"] == 1
    t2 = {**t, "enrolments": t["enrolments"].copy()}
    t2["enrolments"]["section"] = ["A"] * 29 + ["B"] * 29 + ["C"] * 2              # section C has 2 students
    p2 = analyze_course(t2, COURSE, TERM, recall=False)
    assert p2.suppressed["sections_hidden"] == 1
    assert all(s.section != "C" for c in p2.section_comparison for s in c.sections)


def test_student_gaps_are_mentor_only_and_class_sections_have_no_ids(demo):
    _, p = demo
    d = p.to_dict()
    assert d["student_gaps"]["audience"] == "mentor" and d["student_gaps"]["students"]
    rest = json.dumps({k: v for k, v in d.items() if k != "student_gaps"})
    assert "S001" not in rest and "student_id" not in rest


# ---- planted patterns ----------------------------------------------------------------------------
def test_planted_patterns_are_found(demo):
    _, p = demo
    co = {c.co_id: c for c in p.co_attainment}
    assert co["CO3"].gap_type == "teaching_gap" and co["CO3"].level == 0
    assert co["CO2"].gap_type == "student_gap"
    assert co["CO1"].level >= 2
    q7 = next(m for m in p.misconceptions if m.question_id == "Q7")
    assert q7.option == "B" and q7.flagged and 55 <= q7.share_pct <= 62
    assert any(b.co_id == "CO4" for b in p.bloom["insights"])
    lrn = p.learnings[0]
    assert (lrn.co_id, lrn.section, lrn.improved) == ("CO3", "A", True) and lrn.after_level > lrn.before_level
    assert next(t for t in p.trends if t.co_id == "CO5").status == "declining"
    codes = {r.code for r in p.recommendations}
    assert {"RETEACH", "REMEDIAL", "MISCONCEPTION", "BLOOM", "WORKED"} <= codes
    assert next(r for r in p.recommendations if r.code == "RETEACH").text.startswith("Re-teach CO3 (Recursion): only ")


# ---- rolling link ----------------------------------------------------------------------------------
def _insight(sid, course, term):
    return SimpleNamespace(student_id=sid, course_id=course, term_id=term, reasons=[])


def test_rolling_payload_unchanged_without_co_data():
    payload = SimpleNamespace(as_of_day=60, students=[_insight("A", "C", "T")])
    assert add_co_reasons(payload, tiny_tables()).students[0].reasons == []


def test_rolling_payload_gets_weak_co_reason_and_respects_as_of(demo):
    t, _ = demo
    sid = student_co_features(t, COURSE, TERM).sort_values("weakest_co_pct").iloc[0]["student_id"]
    payload = SimpleNamespace(as_of_day=200, students=[_insight(sid, COURSE, TERM), _insight("nobody", COURSE, TERM)])
    r = add_co_reasons(payload, t).students
    assert r[0].reasons[0].text.startswith("Weak on CO") and r[0].reasons[0].group == "co_attainment"
    assert r[1].reasons == []
    early = student_co_features(t, COURSE, TERM, as_of=30)      # only IA1 is due
    assert len(early) == 60 and early["weakest_co_pct"].mean() != student_co_features(t, COURSE, TERM)["weakest_co_pct"].mean()


# ---- Meko hooks -------------------------------------------------------------------------------------
class FakeMeko:
    def __init__(self, memories=(), knowledge=()):
        self.written, self.promoted = [], []
        self.memories, self.knowledge = list(memories), list(knowledge)
        self.last_memory_id = None

    def remember(self, text, tags=None, metadata=None):
        self.written.append({"text": text, "tags": tags, "metadata": metadata})
        self.last_memory_id = f"new{len(self.written)}"
        self.memories.append({"id": self.last_memory_id, "memory": f"{text} [tags: {', '.join(tags or [])}]"})
        return True

    def search_memories(self, query, limit=20):
        return self.memories

    def search_knowledge(self, query, limit=5):
        return self.knowledge

    def promote(self, ids):
        self.promoted.append(ids)
        return ids


def test_course_memories_are_aggregate_only(demo, monkeypatch):
    _, p = demo
    fake = FakeMeko()
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    d = p.to_dict()
    assert d["student_gaps"]["students"]                            # the payload does hold student ids ...
    n = meko_hooks.record_course_learnings(d)
    assert n == len(fake.written) >= 4                              # class + 2 sections + a learning
    blob = json.dumps(fake.written)
    assert "S0" not in blob and "student_id" not in blob       # ... but memories never do
    first = fake.written[0]["text"]
    assert first.startswith(f"{COURSE} {TERM}: ") and "CO3 Recursion attainment level 0" in first
    assert "teaching gap on Q4" in first and "misconception Q7 option B 58%" in first
    assert any(w["text"].startswith(f"{COURSE} {TERM} sec A: ") for w in fake.written)
    assert any("CO3 Recursion improved from level 0 to 3 after re-teach with worked examples" in w["text"] for w in fake.written)


def test_learning_promoted_only_when_it_recurs(demo, monkeypatch):
    _, p = demo
    fake = FakeMeko()
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    meko_hooks.record_course_learnings(p.to_dict())
    assert fake.promoted == []                                      # first sighting: nothing to promote
    past = {"id": "old1", "memory": f"{COURSE} 2025-odd sec B: CO3 Recursion improved from level 1 to 2 after re-teach with "
                                     "worked examples (45% to 66%). [tags: course-learning, ml, course:CS201, term:2025-odd, "
                                     "co:CO3, action:re-teach-with-worked-examples, outcome:improved]"}
    fake = FakeMeko(memories=[past])
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    meko_hooks.record_course_learnings(p.to_dict())
    assert len(fake.promoted) == 1 and "old1" in fake.promoted[0]


def test_recalled_context_passes_through_verbatim(monkeypatch):
    t = make_tables()
    past = f"{COURSE} 2025-odd: CO3 Recursion attainment level 1; teaching gap on Q4. [tags: course-summary, ml, course:{COURSE}]"
    kb = "  promoted KB chunk for CS201 — keep   spacing & punctuation!  "
    fake = FakeMeko(memories=[{"id": "m-42", "memory": past}, {"id": "x", "memory": "unrelated course ME101 note"}],
                    knowledge=[{"document_id": "doc-7", "chunk_text": kb}])
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    p = analyze_course(t, COURSE, TERM)
    assert p.context["recalled"] == [{"id": "m-42", "source": "memory", "text": past},
                                     {"id": "doc-7", "source": "knowledge", "text": kb}]
    assert p.context["meko"] == "active"
    rec = next(r for r in p.recommendations if r.code == "RECURRING")      # CO3 was weak in 2025-odd as well
    assert "2025-odd" in rec.text and rec.co_id == "CO3"


def test_meko_off_is_a_noop(demo, monkeypatch):
    _, p = demo
    monkeypatch.setattr(meko_hooks, "_meko", lambda: None)
    assert meko_hooks.record_course_learnings(p.to_dict()) == 0
    assert meko_hooks.recall_course_history(COURSE) == []
    assert analyze_course(make_tables(), COURSE, TERM).context == {"meko": "off", "recalled": []}


# ---- schema ----------------------------------------------------------------------------------------------
def test_schema_checks_co_tables():
    t = hand({"Q1": [5] * 6})
    bad = {**t, "questions": t["questions"].assign(bloom_level=9)}
    with pytest.raises(ValueError, match="bloom_level"):
        validate(bad)
    over = {**t, "question_results": t["question_results"].assign(marks=99)}
    with pytest.raises(ValueError, match="max_marks"):
        validate(over)
    assert validate({"enrolments": t["enrolments"], "assessments": t["assessments"]})["questions"].empty   # CO tables optional
