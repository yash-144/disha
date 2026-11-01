import json

from disha_ml import meko_hooks


def test_hooks_are_noops_without_key(monkeypatch):
    monkeypatch.delenv("MEKO_API_KEY", raising=False)
    monkeypatch.setattr(meko_hooks, "_client", None)
    assert meko_hooks._meko() is None
    assert meko_hooks.recall_prior_runs("dropout", "hgb", "x.csv") is None
    assert meko_hooks.record_training([], None, "x.csv", "out") is None


def test_disable_flag(monkeypatch):
    monkeypatch.setattr(meko_hooks, "_disabled", False)
    meko_hooks.disable()
    assert meko_hooks._meko() is None


# ---- rolling academic journey (one Meko conversation per student) -------------------------
class FakeClient:
    journey_ready = True
    cfg = type("Cfg", (), {"journey_max_students": 200})()

    def __init__(self):
        self.turns = []

    async def journey_post(self, turns):
        self.turns += turns
        return len(turns)


class FakeMeko:
    def __init__(self):
        self.client = FakeClient()


def _student(sid, tier, prev, events=()):
    return {"student_id": sid, "course_id": "C1", "term_id": "T1", "as_of_day": 120, "last_assessment": "TMA3",
            "risk": {"tier": tier, "previous_tier": prev, "probability": 0.42},
            "reasons": [{"text": "Missed 2 of the last 3 assessments"}, {"text": "Online activity down 60% over the last 2 weeks vs their own earlier rate"}],
            "drift_events": [{"code": c, "text": "First missed submission (by TMA3)"} for c in events],
            "snapshot": {"mean_score": 48.0, "class_median_score": 66.0, "last_score": 40.0, "standing_pct": 18.0}}


def test_assessment_updates_every_student_plus_tier_and_drift_turns(monkeypatch):
    fake = FakeMeko()
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    payload = {"students": [_student("RAW-1001", "HIGH", "MEDIUM"), _student("RAW-1002", "WATCH", "WATCH"),
                            _student("RAW-1003", "WATCH", "WATCH", events=["FIRST_MISSED_SUBMISSION"]),
                            _student("RAW-1004", "ON_TRACK", None)]}
    assert meko_hooks.record_assessment_updates(payload) == 4 + 1 + 1       # 4 updates, 1 tier change, 1 drift event
    meko_hooks.flush()
    kinds = [t["metadata"]["event_type"] for t in fake.client.turns]
    assert kinds.count("assessment_update") == 4 and kinds.count("tier_change") == 1 and kinds.count("drift_event") == 1
    t = next(t for t in fake.client.turns if t["student"] == "RAW-1002")
    assert t["input"].startswith("The student scored 40% on TMA3 in C1 (T1, day 120)")
    assert "Missed 2 of the last 3" in t["output"] and t["metadata"]["assessment_id"] == "TMA3"


def test_assessment_updates_need_salt_and_respect_cap(monkeypatch):
    fake = FakeMeko()
    fake.client.journey_ready = False
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    assert meko_hooks.record_assessment_updates({"students": [_student("RAW-1", "HIGH", "WATCH")]}) == 0
    assert fake.client.turns == []
    fake.client.journey_ready = True
    fake.client.cfg = type("Cfg", (), {"journey_max_students": 1})()
    n = meko_hooks.record_assessment_updates({"students": [_student("RAW-1", "WATCH", "WATCH"), _student("RAW-2", "HIGH", "WATCH")]})
    meko_hooks.flush()
    assert n == 2 and {t["student"] for t in fake.client.turns} == {"RAW-2"}  # the changed student wins the one slot


def test_assessment_updates_noop_when_meko_off(monkeypatch):
    monkeypatch.setattr(meko_hooks, "_meko", lambda: None)
    assert meko_hooks.record_assessment_updates({"students": [_student("RAW-1", "HIGH", "WATCH")]}) == 0
