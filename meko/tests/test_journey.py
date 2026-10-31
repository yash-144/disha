"""Student academic journey: one conversation per student, event turns, privacy, cap, read/correct/forget."""
import json
import re
from types import SimpleNamespace as NS

import pytest

from disha_meko import journey as J
from disha_meko.client import JOURNEY_AGENT, _JOURNEY_IDS
from test_meko import DP_ID, FakeSession, make_client

SALT = "unit-salt"


class JourneySession(FakeSession):
    """Stateful: conversations keyed by session_id (like Meko's dedup), messages kept per conversation."""

    def __init__(self):
        super().__init__()
        self.convs, self.msgs, self.ctx = {}, {}, {}

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        out = None
        if name == "conversation_create":
            sid = args["session_id"]
            if sid not in self.convs:
                self.convs[sid] = {"id": f"conv-{len(self.convs) + 1}", "title": args["title"], "metadata": args["metadata"]}
                self.msgs[self.convs[sid]["id"]] = []
            out = {"id": self.convs[sid]["id"]}
        elif name == "conversation_list":
            out = {"conversations": list(self.convs.values())[args.get("offset", 0):args.get("offset", 0) + args["limit"]]}
        elif name == "conversation_add_message":
            self.msgs[args["conversation_id"]].append(args)
            out = {"message_id": "m"}
        elif name == "conversation_get":
            out = {"messages": [{"input": a["input"], "output": a["output"], "reasoning": a.get("reasoning"),
                                 "metadata": str(json.loads(a["metadata"]))} for a in self.msgs[args["conversation_id"]]]}
        elif name == "context_search":
            out = {"results": self.ctx}
        elif name == "memory_search":
            out = {"results": [{"id": "mem-9", "memory": "Student s scored 48% on TMA3"}]}
        if out is None:
            return await super().call_tool(name, args)
        return NS(is_error=False, content=[NS(text=json.dumps(out))], structured_content=None)


@pytest.fixture(autouse=True)
def _reset():
    _JOURNEY_IDS.clear()


def mk(**cfg):
    s = JourneySession()
    c, s = make_client(s, journey_delay=0, **{"pii_salt": SALT, **cfg})
    return c, s


def adds(s):
    return s.calls_to("conversation_add_message")


async def test_one_conversation_per_student_reused():
    c, s = mk()
    t = [J.assessment_update_turn("RAW-1", course="C1", term="T1", day=10, assessment="TMA1", score_pct=60),
         J.assessment_update_turn("RAW-1", course="C1", term="T1", day=20, assessment="TMA2", score_pct=50),
         J.assessment_update_turn("RAW-2", course="C1", term="T1", day=20, assessment="TMA2", score_pct=70)]
    assert await c.journey_post(t) == 3
    assert await c.journey_post(t[:1]) == 1                                 # later call reuses the cache
    assert len(s.calls_to("conversation_create")) == 2                       # two students, two conversations
    cr = s.calls_to("conversation_create")[0]
    h = c.hash_id("RAW-1")
    assert cr["title"] == f"journey:{h}" and cr["agent_id"] == JOURNEY_AGENT and cr["session_id"] == f"journey:{h}"
    assert json.loads(cr["metadata"]) == {"kind": "journey", "student": h}
    assert await c.journey_conversation("RAW-1") == await c.journey_conversation(h)   # hashed or raw id: same conversation


async def test_existing_conversation_found_via_list_after_restart():
    c, s = mk()
    await c.journey_post([J.assessment_update_turn("RAW-1", course="C1", term="T1", day=1, assessment="A1")])
    _JOURNEY_IDS.clear()                                                     # new process, same Meko
    c2, _ = make_client(s, journey_delay=0, pii_salt=SALT)
    assert await c2.journey_conversation("RAW-1", create=False) == "conv-1"
    assert len(s.calls_to("conversation_create")) == 1                       # found by conversation_list, not re-created


EVENTS = {
    "admission_baseline": lambda: J.admission_baseline_turn("R", programme="BTech CSE", level="UG", tenth_pct=82, twelfth_pct=76, entrance_pct=91, year=1),
    "assessment_update": lambda: J.assessment_update_turn("R", course="CS201", term="2026-odd", day=120, assessment="TMA3", score_pct=48,
                                                          class_median=66, standing_pct=18, mean_pct=52, risk=0.42, tier="MEDIUM",
                                                          previous_tier="WATCH", reasons=["Missed 2 of the last 3 assessments"]),
    "tier_change": lambda: J.tier_change_turn("R", course="CS201", term="2026-odd", day=120, assessment="TMA3", previous_tier="WATCH", tier="HIGH", risk=0.7),
    "drift_event": lambda: J.drift_event_turn("R", course="CS201", term="2026-odd", day=120, assessment="TMA3", code="SCORE_DROP", text="Score fell 20 points on TMA3"),
    "term_summary": lambda: J.term_summary_turn("R", term="2026-odd", tier="MEDIUM", courses=[
        {"course": "CS201", "mean_pct": 55, "trend": "declining", "weak_cos": [{"co": "CO3", "description": "Recursion", "pct": 35}]}]),
    "case_event": lambda: J.case_event_turn("R", case_id="case-1", event="opened", tier="HIGH", reason_codes=["LOW_SCORES"]),
    "intervention": lambda: J.intervention_turn("R", intervention_id="mentor_call", case_id="case-1", reason_codes=["LOW_SCORES"]),
    "outcome": lambda: J.outcome_turn("R", outcome="improved", intervention_id="mentor_call", case_id="case-1"),
    "mentor_note": lambda: J.mentor_note_turn("R", text="Struggles with recursion but attends every tutorial.", course="CS201"),
}


@pytest.mark.parametrize("event", sorted(EVENTS))
async def test_every_event_type_posts_a_full_turn(event):
    c, s = mk()
    assert await c.journey_post([EVENTS[event]()]) == 1
    a = adds(s)[0]
    assert a["input"] and a["output"] and a["reasoning"] and a["seed"].startswith("journey:")
    assert a["agent_id"] == JOURNEY_AGENT and a["datapack_id"] == DP_ID
    meta = json.loads(a["metadata"])
    assert meta["event_type"] == event and meta["student"] == c.hash_id("R") and meta["kind"] == "journey"
    assert "R" not in re.findall(r"\bR\b", a["input"] + a["output"])         # raw id never in the text


def test_assessment_update_is_one_short_sentence_with_standing_and_metadata():
    t = EVENTS["assessment_update"]()
    assert t["input"] == ("The student scored 48% on TMA3 in CS201 (2026-odd, day 120), 18 points below the class median "
                          "of 66%, 18th percentile in the class and submitted late.".replace(" and submitted late", ""))
    assert "MEDIUM" not in t["input"] and "medium risk" in t["output"] and "Missed 2 of the last 3" in t["output"]
    assert t["metadata"] == {"event_type": "assessment_update", "course": "CS201", "term": "2026-odd", "day": 120,
                             "assessment_id": "TMA3", "tier": "MEDIUM", "risk": 0.42}
    m = J.assessment_update_turn("R", course="C", term="T", day=5, assessment="A1", missed=True)
    assert m["input"].startswith("The student missed A1") and m["metadata"]["missed"] is True
    assert "submitted late" in J.assessment_update_turn("R", course="C", term="T", day=5, assessment="A1", score_pct=50, late=True)["input"]


async def test_salt_required_refuses_to_write(caplog):
    c, s = make_client(JourneySession(), pii_salt="")
    assert c.journey_ready is False
    assert await c.journey_post([EVENTS["assessment_update"]()]) == 0
    assert await c.journey_conversation("RAW") == "" and await c.journey_timeline("RAW") == []
    assert s.calls == []                                                    # nothing reached Meko


async def test_pii_guard_on_every_text():
    c, s = mk()
    dirty = {"student": "RAW-1001", "input": "RAW-1001 (asha@x.edu, +91 98765 43210) failed", "output": "ok RAW-1001",
             "reasoning": "call 98765 43210", "metadata": {"event_type": "x", "name": "Asha", "email": "a@b.co"}}
    assert await c.journey_post([dirty]) == 1
    blob = json.dumps(adds(s)[0])
    for bad in ("RAW-1001", "asha@x.edu", "98765 43210", "a@b.co", "Asha"):
        assert bad not in blob
    note = J.mentor_note_turn("R", text="Call parent at +91 98765 43210 or mum@home.in; roll CS2021-042 needs help in CS201", course="CS201")
    assert "98765" not in note["input"] and "@" not in note["input"] and "2021-042" not in note["input"] and "CS201" in note["input"]
    assert len(J.mentor_note_turn("R", text="x " * 600)["input"]) < 500
    assert J.mentor_note_turn("R", text="1 2 3\n4 5 6\n7 8 9\n") is None   # a mark table is refused
    assert J.mentor_note_turn("R", text="  ") is None


async def test_cap_on_students():
    c, s = mk(journey_max_students=2)
    t = [J.assessment_update_turn(f"RAW-{i}", course="C", term="T", day=1, assessment="A1") for i in range(4)]
    assert await c.journey_post(t) == 2
    assert len(s.calls_to("conversation_create")) == 2
    assert await c.journey_post([J.assessment_update_turn("RAW-0", course="C", term="T", day=2, assessment="A2")]) == 1  # already open: allowed


def test_turns_from_insights_every_student_and_cap_priority():
    def st(i, tier, prev, p, ev=()):
        return {"student_id": f"RAW-{i}", "course_id": "C1", "term_id": "T1", "as_of_day": 30, "last_assessment": "TMA1",
                "risk": {"tier": tier, "previous_tier": prev, "probability": p},
                "reasons": [{"text": "r1"}], "drift_events": [{"code": c, "text": "t"} for c in ev],
                "snapshot": {"last_score": 55.0, "class_median_score": 60.0, "standing_pct": 40.0, "mean_score": 55.0, "consecutive_misses": 0}}
    payload = {"students": [st(1, "ON_TRACK", "ON_TRACK", 0.1), st(2, "HIGH", "WATCH", 0.8), st(3, "WATCH", "WATCH", 0.3, ["SCORE_DROP"])]}
    kinds = [t["metadata"]["event_type"] for t in J.turns_from_insights(payload)]
    assert kinds.count("assessment_update") == 3 and kinds.count("tier_change") == 1 and kinds.count("drift_event") == 1
    capped = J.turns_from_insights(payload, 2)
    assert {t["student"] for t in capped} == {"RAW-2", "RAW-3"}                # changed/drifted students first


async def test_timeline_in_order_and_briefing_verbatim_scoped():
    c, s = mk()
    await c.journey_post([J.assessment_update_turn("RAW-1", course="C", term="T", day=d, assessment=f"A{d}", score_pct=50) for d in (1, 2, 3)])
    tl = await c.journey_timeline("RAW-1", 10)
    assert [t["metadata"]["day"] for t in tl] == [1, 2, 3]
    s.ctx = {"memory": [{"id": "mem-1", "memory": "Scored 48% on TMA3", "run_id": "conv1"},          # this student (dashes ignored)
                        {"id": "mem-2", "memory": "Another student failed", "run_id": "conv-2"}],
             "knowledge_base": [{"chunk_text": "generic policy"}],
             "conversation": {"hits": [{"id": "t1", "output": "Risk rose", "conversation_id": "conv-1"},
                                       {"output": "unrelated", "conversation_id": "conv-2"}]}}
    b = await c.journey_briefing("RAW-1", "how is the student doing?")
    got = {(i["id"], i["source"], i["text"]) for i in b["items"]}
    assert got == {("mem-9", "memory", "Student s scored 48% on TMA3"), ("mem-1", "memory", "Scored 48% on TMA3"),
                   ("t1", "conversation", "Risk rose")}                          # verbatim, only this student's
    ctx = s.calls_to("context_search")[0]
    assert ctx["query"] == "how is the student doing?" and ctx["conversation_id"] == "conv-1"
    assert s.calls_to("memory_search")[0]["run_id"] == "conv-1"


async def test_meko_off_returns_empty_without_calls():
    c, s = mk()
    b = await J.journey_briefing(c, "RAW-1", "q", meko_enabled=False)
    assert b["enabled"] is False and b["items"] == [] and await J.journey_timeline(c, "RAW-1", meko_enabled=False) == []
    assert s.calls == []
    off, s2 = make_client(JourneySession(), api_key="", pii_salt=SALT)       # no key: Meko inactive
    assert (await off.journey_briefing("RAW-1"))["items"] == [] and await off.journey_post([EVENTS["tier_change"]()]) == 0
    assert s2.calls == []


async def test_correct_and_forget_call_the_right_tools():
    c, s = mk()
    assert await J.correct_memory(c, "mem-1", "Scored 58% on TMA3, mail me at a@b.co") is True
    up = s.calls_to("memory_update")[0]
    assert up["memory_id"] == "mem-1" and up["agent_id"] == JOURNEY_AGENT and up["datapack_id"] == DP_ID
    assert "a@b.co" not in up["text"] and up["text"].startswith("Scored 58%")
    assert await J.forget_memory(c, "mem-2") is True
    de = s.calls_to("memory_delete_by_id")[0]
    assert de["memory_id"] == "mem-2" and de["agent_id"] == JOURNEY_AGENT
    assert await J.forget_memory(c, "") is False and await J.correct_memory(c, "mem-1", "") is False


async def test_write_retries_once_and_fails_softly():
    c, s = mk()
    boom = {"n": 0}
    orig = s.call_tool

    async def flaky(name, args):
        if name == "conversation_add_message" and boom["n"] < 1:
            boom["n"] += 1
            raise ConnectionError("dropped")
        return await orig(name, args)
    s.call_tool = flaky
    import asyncio
    real = asyncio.sleep
    asyncio.sleep = lambda *_a, **_k: real(0)
    try:
        assert await c.journey_post([EVENTS["tier_change"]()]) == 1          # second attempt lands
    finally:
        asyncio.sleep = real


async def test_erase_student_deletes_extracted_memories_then_conversation():
    c, s = mk()
    await c.journey_post([J.tier_change_turn("RAW-1", course="C", term="T", day=1, assessment="A1", previous_tier="WATCH", tier="HIGH")])
    pages = [[{"id": "m1", "run_id": "conv1"}, {"id": "m2", "run_id": "conv-1"}, {"id": "other", "run_id": "conv-2"}]]
    orig = s.call_tool

    async def call_tool(name, args):
        if name == "memory_search":
            s.calls.append((name, args))
            rows = pages[0] if pages and not s.calls_to("memory_delete_by_id") else []
            return NS(is_error=False, content=[NS(text=json.dumps({"results": rows}))], structured_content=None)
        return await orig(name, args)
    s.call_tool = call_tool
    out = await J.erase_student(c, "RAW-1")
    assert out["memories_deleted"] == 2 and out["conversation_deleted"] is True
    deleted = {a["memory_id"] for a in s.calls_to("memory_delete_by_id")}
    assert deleted == {"m1", "m2"}                                   # never another student's memory
    assert all(a["run_id"] == "conv-1" for a in s.calls_to("memory_search"))
    names = [n for n, _ in s.calls]
    assert names.index("conversation_delete") > max(i for i, n in enumerate(names) if n == "memory_delete_by_id")
    assert await c.journey_conversation("RAW-1", create=False) == ""   # cache cleared


async def test_erase_student_needs_salt_and_known_journey():
    c, s = mk(pii_salt="")
    assert (await c.erase_student("RAW-1"))["conversation_deleted"] is False and s.calls == []
    c2, s2 = mk()
    assert (await c2.erase_student("RAW-404")) == {"student": c2.journey_hash("RAW-404"), "memories_deleted": 0, "conversation_deleted": False}
