# utils/scoring.py

import random
import hashlib

PARAGON_DIMENSIONS = [
    "Policy Engagement & Expertise",
    "Accountability & Transparency",
    "Representation & Responsiveness",
    "Assertiveness & Influence",
    "Governance & Institutional Strength",
    "Organizational & Party Cohesion",
    "Narrative & Communication",
]

def deterministic_score(seed: str) -> int:
    """Generates a stable score (0-100) for the same input."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    return int(h[:2], 16)  # 2 hex chars → 0–255 → scaled below


def generate_paragon_scores(name: str, category: str, zodiac: str):
    """
    Fully dynamic scoring engine.
    Uses name + category + zodiac as a stable seed.
    Produces:
      - overall score
      - 7 PARAGON dimension scores
    """

    dimensions = {}
    base_seed = f"{name}-{category}-{zodiac}"

    for dim in PARAGON_DIMENSIONS:
        raw = deterministic_score(base_seed + dim)
        score = round((raw / 255) * 100)  # scale to 0–100
        dimensions[dim] = score

    overall = round(sum(dimensions.values()) / len(dimensions))

    return {
        "overall": overall,
        "dimensions": dimensions,
    }
