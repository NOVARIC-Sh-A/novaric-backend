# utils/scoring.py
from typing import Dict
from .paragon_constants import PARAGON_DIMENSIONS

def generate_paragon_scores(
    name: str,
    category: str,
    zodiac: str = "Unknown",
) -> Dict[str, Dict[str, int] | int]:
    """
    PARAGON® Engine v1 – beginner-friendly version.
    - Uses fixed baseline scores per dimension.
    - Adds small adjustments based on category/zodiac.
    - Always returns:
        {
          "overall": int (0–100),
          "dimensions": { dim: int }
        }
    """

    # 1) Baseline scores per dimension
    baseline: Dict[str, int] = {
        "Policy Engagement & Expertise": 65,
        "Accountability & Transparency": 50,
        "Representation & Responsiveness": 60,
        "Assertiveness & Influence": 70,
        "Governance & Institutional Strength": 55,
        "Organizational & Party Cohesion": 62,
        "Narrative & Communication": 68,
    }

    # 2) Simple adjustments by category (you can refine later)
    category_adjustments: Dict[str, Dict[str, int]] = {
        "political": {
            "Policy Engagement & Expertise": +5,
            "Accountability & Transparency": -3,
        },
        "media": {
            "Narrative & Communication": +7,
        },
    }

    # 3) Copy baseline into final_scores
    final_scores: Dict[str, int] = baseline.copy()

    # 4) Apply category adjustments if exist
    adjustments = category_adjustments.get(category, {})
    for dim, delta in adjustments.items():
        if dim in final_scores:
            final_scores[dim] = max(0, min(100, final_scores[dim] + delta))

    # 5) Optional micro tweak by zodiac (just to show logic – can be removed)
    if zodiac == "Aries":
        final_scores["Assertiveness & Influence"] = min(
            100, final_scores["Assertiveness & Influence"] + 5
        )

    # 6) Compute overall as weighted average
    # For v1, all dimensions weight = 1 (simple average)
    scores_list = [final_scores[d] for d in PARAGON_DIMENSIONS]
    overall = round(sum(scores_list) / len(scores_list))

    return {
        "overall": overall,
        "dimensions": final_scores,
    }
