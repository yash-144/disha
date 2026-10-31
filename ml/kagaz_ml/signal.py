"""Combine model probability and academic rules into a risk tier.

HIGH      p >= high cutoff                              -> signal raised
MEDIUM    medium cutoff <= p < high cutoff AND >=1 rule  -> signal raised
WATCH     p >= watch cutoff, or MEDIUM band with no rule -> listed, no signal
ON_TRACK  everything else

Then a capacity cap: if signals exceed `capacity_share` of the cohort, only the
highest-probability ones keep their signal; the rest become WATCH. The cap keeps
the number of signals within what advisors can act on.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

TIERS = ("HIGH", "MEDIUM", "WATCH", "ON_TRACK")


def _t(cut: Optional[Dict]) -> float:
    return cut["threshold"] if cut else np.inf


def assign_tiers(p, rule_counts, cutoffs: Dict, capacity_share: float):
    p = np.asarray(p, dtype=float)
    rules = np.asarray(rule_counts, dtype=float)
    t_high, t_med, t_watch = _t(cutoffs.get("high")), _t(cutoffs.get("medium")), _t(cutoffs.get("watch"))

    tier = np.full(len(p), "ON_TRACK", dtype=object)
    tier[p >= t_watch] = "WATCH"
    in_medium_band = (p >= t_med) & (p < t_high)
    tier[in_medium_band] = "WATCH"
    tier[in_medium_band & (rules >= 1)] = "MEDIUM"
    tier[p >= t_high] = "HIGH"

    signal = np.isin(tier, ["HIGH", "MEDIUM"])
    capped = np.zeros(len(p), dtype=bool)
    limit = int(np.floor(capacity_share * len(p)))
    if len(p) and signal.sum() > max(limit, 1):
        idx = np.nonzero(signal)[0]
        keep = idx[np.argsort(-p[idx], kind="mergesort")[:max(limit, 1)]]
        drop = np.setdiff1d(idx, keep)
        tier[drop] = "WATCH"
        signal[drop] = False
        capped[drop] = True
    return tier, signal, capped
