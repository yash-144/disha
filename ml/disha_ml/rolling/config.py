"""All tunable numbers of the rolling model, in one place (recorded in the manifest)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Tuple

from ..config import TierConfig

# Academic rules: MEDIUM needs at least one to fire. Same thresholds drive the reason texts.
RULES: Dict[str, float] = {
    "MISSED_LAST3": 2,         # missed >= 2 of the last 3 assessments
    "BELOW_MEDIAN_PTS": -15.0,  # mean score this far (points) below the class median
    "ENGAGEMENT_RATIO": 0.5,    # last-14-day activity <= half of the student's own earlier rate
    "SCORE_DROP_PTS": -10.0,    # last score this far below the previous one
    "BELOW_BASELINE_PTS": -25.0,  # percentile gap to entry baseline
    "CONSECUTIVE_MISSES": 2,
}
# Student drift events (sudden changes between two snapshots).
DRIFT: Dict[str, float] = {"SCORE_DROP_PTS": 15.0, "ENGAGEMENT_COLLAPSE_RATIO": 0.4}
DELTA_STEADY = 0.05      # |change in risk| below this is "steady"
MIN_EFFECT = 0.02        # a feature group must move risk by >= 2 points to be a reason
PSI_WATCH, PSI_SHIFT = 0.1, 0.2
RECENT_DAYS = 14


@dataclass
class RollingConfig:
    train_terms: Tuple[str, ...] = ("2013B", "2013J", "2014B")
    test_terms: Tuple[str, ...] = ("2014J",)
    fixed_fracs: Tuple[float, ...] = (0.1, 0.25, 0.5, 0.75)   # fixed-day snapshots, share of term
    calibration: str = "isotonic"
    cv_folds: int = 5
    seed: int = 42
    # More signals allowed than the semester model: ~45% of active OULAD students end at risk.
    tiers: TierConfig = field(default_factory=lambda: TierConfig(capacity_share=0.25))

    def to_dict(self) -> Dict:
        return asdict(self)
