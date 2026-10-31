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


# ---- rolling academic-story memories ----------------------------------------------
class FakeMeko:
    def __init__(self):
        self.memories = []

    def hash_id(self, v):
        return "s_" + "x" * 12

    def remember(self, text, tags=None, metadata=None):
        self.memories.append({"text": text, "tags": tags, "metadata": metadata})
        return True


def _student(sid, tier, prev, events=()):
    return {"student_id": sid, "course_id": "C1", "term_id": "T1", "as_of_day": 120, "last_assessment": "TMA3",
            "risk": {"tier": tier, "previous_tier": prev},
            "reasons": [{"text": "Missed 2 of the last 3 assessments"}, {"text": "Online activity down 60% over the last 2 weeks vs their own earlier rate"}],
            "drift_events": [{"code": c, "text": "First missed submission (by TMA3)"} for c in events],
            "snapshot": {"mean_score": 48.0, "class_median_score": 66.0}}


def test_assessment_updates_written_only_on_change_and_redacted(monkeypatch):
    fake = FakeMeko()
    monkeypatch.setattr(meko_hooks, "_meko", lambda: fake)
    payload = {"students": [_student("RAW-1001", "HIGH", "MEDIUM"), _student("RAW-1002", "WATCH", "WATCH"),
                            _student("RAW-1003", "WATCH", "WATCH", events=["FIRST_MISSED_SUBMISSION"]),
                            _student("RAW-1004", "ON_TRACK", None)]}
    assert meko_hooks.record_assessment_updates(payload) == 2                # 1001 changed, 1003 drifted; 1002/1004 skipped
    first = fake.memories[0]
    assert first["text"].startswith("Assessment update (day 120, TMA3): mean 48% (class median 66%); risk MEDIUM→HIGH;")
    assert "Missed 2 of the last 3" in first["text"]
    blob = json.dumps(fake.memories)
    assert "RAW-100" not in blob and "journey:s_xxxxxxxxxxxx" in first["tags"]
    assert first["metadata"]["student"] == "s_xxxxxxxxxxxx"


def test_assessment_updates_noop_when_meko_off(monkeypatch):
    monkeypatch.setattr(meko_hooks, "_meko", lambda: None)
    assert meko_hooks.record_assessment_updates({"students": [_student("RAW-1", "HIGH", "WATCH")]}) == 0
