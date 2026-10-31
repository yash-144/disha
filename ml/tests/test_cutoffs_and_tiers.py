import numpy as np

from kagaz_ml.config import TierConfig
from kagaz_ml.signal import assign_tiers
from kagaz_ml.thresholds import choose_cutoff, choose_tier_cutoffs


def test_cutoff_meets_precision_target_and_is_stable():
    # Top 40 scores: 38 positives. Next 60: 30 positives. Rest: 2 of 100.
    p = np.r_[np.linspace(0.99, 0.80, 40), np.linspace(0.79, 0.40, 60), np.linspace(0.39, 0.01, 100)]
    y = np.r_[[1] * 38 + [0] * 2, [1, 0] * 30, [1] * 2 + [0] * 98]
    c = choose_cutoff(y, p, target_precision=0.90, min_alerts=10)
    assert c is not None
    assert c["precision"] >= 0.90
    assert c["threshold"] >= 0.70           # stops before the 50%-precision band
    flagged = p >= c["threshold"]
    assert y[flagged].mean() >= 0.90


def test_cutoff_none_when_target_unreachable():
    rng = np.random.default_rng(0)
    p = rng.random(500)
    y = (rng.random(500) < 0.3).astype(int)   # scores carry no information
    assert choose_cutoff(y, p, target_precision=0.85, min_alerts=30) is None


def test_ties_are_flagged_together():
    p = np.array([0.9] * 50 + [0.1] * 50)
    y = np.array([1] * 45 + [0] * 5 + [0] * 50)
    c = choose_cutoff(y, p, target_precision=0.85, min_alerts=10)
    assert c["flagged"] == 50


def test_tier_logic_and_rule_corroboration():
    cut = {"high": {"threshold": 0.8}, "medium": {"threshold": 0.6}, "watch": {"threshold": 0.4}}
    p = np.array([0.9, 0.7, 0.7, 0.5, 0.1])
    rules = np.array([0, 1, 0, 3, 3])
    tier, signal, capped = assign_tiers(p, rules, cut, capacity_share=1.0)
    assert tier.tolist() == ["HIGH", "MEDIUM", "WATCH", "WATCH", "ON_TRACK"]
    assert signal.tolist() == [True, True, False, False, False]
    assert not capped.any()


def test_capacity_cap_keeps_highest_scores():
    cut = {"high": {"threshold": 0.5}, "medium": None, "watch": None}
    p = np.linspace(0.99, 0.51, 10)
    tier, signal, capped = assign_tiers(p, np.zeros(10), cut, capacity_share=0.3)
    assert signal.sum() == 3
    assert signal[:3].all()
    assert capped.sum() == 7 and (tier[3:] == "WATCH").all()


def test_disabled_tiers_raise_no_signal():
    tier, signal, _ = assign_tiers([0.99], [5], {"high": None, "medium": None, "watch": None}, 1.0)
    assert tier.tolist() == ["ON_TRACK"] and not signal.any()


def test_tier_cutoffs_are_ordered():
    rng = np.random.default_rng(1)
    y = (rng.random(2000) < 0.3).astype(int)
    p = np.clip(0.3 + 0.5 * (y - 0.3) + rng.normal(0, 0.15, 2000), 0, 1)
    c = choose_tier_cutoffs(y, p, TierConfig())
    ts = [c[k]["threshold"] for k in ("watch", "medium", "high") if c[k]]
    assert ts == sorted(ts)
