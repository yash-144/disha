"""Pick probability cutoffs from a precision target.

Rule: walk the cutoff down from the highest score. Accept a cutoff only while
EVERY cutoff above it (with at least `min_alerts` students flagged) still meets
the precision target. Stop at the first violation. This avoids picking a
cutoff that only meets the target because of a lucky narrow band.

Cutoffs are chosen on out-of-fold predictions from the training split and then
checked once on the untouched test split.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np


def precision_by_cutoff(y: np.ndarray, p: np.ndarray):
    """Return (cutoffs desc, flagged count, true positives) at each unique cutoff."""
    order = np.argsort(-p, kind="mergesort")
    p_sorted, y_sorted = p[order], y[order]
    tp_cum = np.cumsum(y_sorted)
    # Last index of each unique score: students tied on a score are flagged together.
    last = np.r_[np.nonzero(np.diff(p_sorted))[0], len(p_sorted) - 1]
    cutoffs = p_sorted[last]
    counts = last + 1
    tps = tp_cum[last]
    return cutoffs, counts, tps


def choose_cutoff(y, p, target_precision: float, min_alerts: int) -> Optional[Dict[str, float]]:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    cutoffs, counts, tps = precision_by_cutoff(y, p)
    positives = max(int(y.sum()), 1)
    chosen = None
    for c, n, tp in zip(cutoffs, counts, tps):
        if n < min_alerts:
            continue
        prec = tp / n
        if prec < target_precision:
            break
        chosen = {
            "threshold": float(c),
            "precision": float(prec),
            "recall": float(tp / positives),
            "flagged": int(n),
            "flag_rate": float(n / len(y)),
        }
    return chosen


def choose_tier_cutoffs(y, p, tiers) -> Dict[str, Optional[Dict[str, float]]]:
    high = choose_cutoff(y, p, tiers.high_precision, tiers.min_alerts)
    medium = choose_cutoff(y, p, tiers.medium_precision, tiers.min_alerts)
    watch = choose_cutoff(y, p, tiers.watch_precision, tiers.min_alerts)
    # Keep tiers ordered: watch <= medium <= high.
    if high and medium and medium["threshold"] > high["threshold"]:
        medium = None
    if medium and watch and watch["threshold"] > medium["threshold"]:
        watch = None
    return {"high": high, "medium": medium, "watch": watch}
