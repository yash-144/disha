"""Small-cell suppression shared by analytics and wellbeing aggregates.

Blueprint 01 FR-ANA-02 / 10 PUL-08: a group below the minimum size is never reported.
The minimum cell size is an open product decision, so it is a named constant per use
(5 for operational cohort analytics, 10 for the wellbeing pulse) rather than a literal.
"""
from typing import Any, Dict, List, Optional

MIN_CELL_SIZE_ANALYTICS = 5
MIN_RESPONDENTS_PULSE = 10


def is_suppressed(n: int, minimum: int) -> bool:
    return n < minimum


def suppress_distribution(counts: Dict[str, int], minimum: int) -> List[Dict[str, Any]]:
    """Turn {label: n} into cells, hiding any cell with 0 < n < minimum.

    Complementary suppression: when exactly one non-empty cell is hidden and the total is
    public, the hidden value could be recovered by subtraction, so the next-smallest
    non-empty cell is hidden too. Zero cells are always shown (they identify nobody).
    """
    cells = [{"label": k, "count": v, "suppressed": False} for k, v in counts.items()]
    hidden = [c for c in cells if 0 < c["count"] < minimum]
    if len(hidden) == 1:
        others = sorted((c for c in cells if c["count"] >= minimum), key=lambda c: c["count"])
        if others:
            hidden.append(others[0])
    for c in hidden:
        c["count"] = None
        c["suppressed"] = True
    return cells


def suppress_value(n: int, value: Any, minimum: int) -> Optional[Any]:
    """Return value only if the group it summarises has at least `minimum` members."""
    return None if n < minimum else value
