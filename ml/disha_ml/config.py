"""Training and signal configuration.

All tunable numbers live here so they are visible in one place and recorded
in each model manifest.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List


# Checkpoints: what is known at each point in time.
#   cp0 = at admission, cp1 = after semester 1, cp2 = after semester 2.
CHECKPOINTS: List[str] = ["cp0", "cp1", "cp2"]


@dataclass
class TierConfig:
    # Precision targets used to pick probability cutoffs on out-of-fold data.
    # HIGH: a signal is raised on probability alone.
    high_precision: float = 0.85
    # MEDIUM: a signal is raised only if an academic rule also fires.
    medium_precision: float = 0.70
    # WATCH: listed for staff, no signal.
    watch_precision: float = 0.50
    # A cutoff is only accepted if at least this many students sit above it.
    min_alerts: int = 30
    # Hard cap on signals per cohort (share of students), sized to advisor capacity.
    capacity_share: float = 0.15


@dataclass
class TrainConfig:
    label: str = "dropout"             # "dropout" or "not_on_time"
    model: str = "hgb"                 # "hgb" or "logreg"
    calibration: str = "isotonic"      # "isotonic" or "sigmoid"
    test_size: float = 0.20
    cv_folds: int = 5
    seed: int = 42
    # Release check: test precision at the HIGH cutoff may fall short of the
    # target by at most this much.
    precision_tolerance: float = 0.05
    tiers: TierConfig = field(default_factory=TierConfig)

    def to_dict(self) -> Dict:
        return asdict(self)


# Academic rules that give human-readable reason codes.
# Values are thresholds; see rules.py for how each is applied.
RULES: Dict[str, float] = {
    "LOW_PASS_RATE": 0.50,       # passed / enrolled below this
    "EXAM_NO_SHOW": 1,           # units with no evaluation >= this
    "FAILED_UNITS": 2,           # enrolled - approved >= this
    "LOW_GRADE": 10.0,           # semester mean grade below this (0-20 scale)
    "GRADE_DROP": 2.0,           # sem2 grade lower than sem1 by at least this
}
