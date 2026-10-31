"""All tunable numbers of the CLO insights, in one place (echoed in the payload as `config`)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, Tuple


@dataclass
class CloConfig:
    default_target_pct: float = 60.0                 # used when course_outcomes has no target_pct
    # share of students (%) reaching the target -> NBA-style level 3 / 2 / 1 (below the last cut: 0)
    level_cuts: Tuple[float, float, float] = (70.0, 60.0, 50.0)
    kind_weights: Dict[str, float] = field(default_factory=lambda: {"internal": 0.4, "end_sem": 0.6})
    end_sem_keywords: Tuple[str, ...] = ("see", "end", "exam", "final")   # assessments.type containing one = end-semester
    top_bottom_frac: float = 0.27                    # item-analysis groups
    teaching_gap_p_top: float = 0.5                  # top group below this = teaching gap
    student_gap_p_top: float = 0.7                   # top group at/above this ...
    student_gap_p_bottom: float = 0.4                # ... and bottom group below this = student gap
    low_discrimination: float = 0.15                 # D below this (and not a ceiling item) = possibly ambiguous
    ceiling_p: float = 0.9                           # very easy questions are allowed to discriminate little
    misconception_share: float = 0.30                # a wrong option chosen by this share is a misconception
    min_group_size: int = 5                          # smaller groups are never shown at class level
    trend_delta_pts: float = 10.0                    # attainment change (points) that counts as improving / declining
    section_gap_pts: float = 15.0                    # attainment spread between sections worth a comment
    bloom_low_max: int = 2                           # Bloom levels <= this are "remember/understand"
    bloom_gap_pts: float = 20.0                      # low-band minus high-band attainment that triggers the insight
    max_recommendations: int = 12

    def to_dict(self) -> Dict:
        return asdict(self)
