# scoring_engine.py

from typing import Dict, Any, List

# ------------------------------------------------------------
# Normalization ranges for metrics (min, max)
# ------------------------------------------------------------
RANGES = {
    "scandals_flagged": (0, 10),            # inverse
    "wealth_declaration_issues": (0, 5),    # inverse
    "public_projects_completed": (0, 50),
    "parliamentary_attendance": (0, 100),
    "international_meetings": (0, 30),
    "party_control_index": (0, 20),
    "media_mentions_monthly": (0, 2000),
    "legislative_initiatives": (0, 20),
    "independence_index": (0, 10),
    "sentiment_score": (-1, 1),
    "social_influence": (0, 10),
    # New event-based momentum range (-10 to +10)
    "momentum_raw": (-10, 10),
}

# ------------------------------------------------------------
# Dimension weights (unchanged for existing 7 dimensions)
# ------------------------------------------------------------
WEIGHTS = {
    "integrity": {
        "scandals_flagged": 0.60,
        "wealth_declaration_issues": 0.40,
    },
    "governance": {
        "public_projects_completed": 0.50,
        "parliamentary_attendance": 0.30,
        "international_meetings": 0.20,
    },
    "influence": {
        "party_control_index": 0.40,
        "media_mentions_monthly": 0.40,
        "social_influence": 0.20,
    },
    "professionalism": {
        "legislative_initiatives": 0.70,
        "independence_index": 0.30,
    },
}

# =====================================================================
# NORMALIZATION FUNCTION
# =====================================================================
def _norm(key: str, value: float, inverse: bool = False) -> float:
    min_v, max_v = RANGES.get(key, (0, 1))
    clamped = max(min_v, min(value, max_v))

    span = max_v - min_v
    score = ((clamped - min_v) / span) * 100 if span > 0 else 0

    return (100 - score) if inverse else score


# =====================================================================
# CORE SCORING ENGINE
# =====================================================================
def score_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts unified metrics into:
        - 8 PARAGON dimensions
        - overall score (0–100)
    """

    # ------------------------------
    # 1. Integrity & Transparency
    # ------------------------------
    s_scandals = _norm("scandals_flagged", metrics.get("scandals_flagged", 0), inverse=True)
    s_wealth = _norm("wealth_declaration_issues", metrics.get("wealth_declaration_issues", 0), inverse=True)

    integrity_score = (
        s_scandals * WEIGHTS["integrity"]["scandals_flagged"] +
        s_wealth * WEIGHTS["integrity"]["wealth_declaration_issues"]
    )

    # ------------------------------
    # 2. Governance Strength
    # ------------------------------
    s_projects = _norm("public_projects_completed", metrics.get("public_projects_completed", 0))
    s_attendance = _norm("parliamentary_attendance", metrics.get("parliamentary_attendance", 0))
    s_intl = _norm("international_meetings", metrics.get("international_meetings", 0))

    governance_score = (
        s_projects * WEIGHTS["governance"]["public_projects_completed"] +
        s_attendance * WEIGHTS["governance"]["parliamentary_attendance"] +
        s_intl * WEIGHTS["governance"]["international_meetings"]
    )

    # ------------------------------
    # 3. Influence & Assertiveness
    # ------------------------------
    s_party = _norm("party_control_index", metrics.get("party_control_index", 0))
    s_media = _norm("media_mentions_monthly", metrics.get("media_mentions_monthly", 0))
    s_social = _norm("social_influence", metrics.get("social_influence", 0))

    influence_score = (
        s_party * WEIGHTS["influence"]["party_control_index"] +
        s_media * WEIGHTS["influence"]["media_mentions_monthly"] +
        s_social * WEIGHTS["influence"]["social_influence"]
    )

    # ------------------------------
    # 4. Professionalism
    # ------------------------------
    s_leg = _norm("legislative_initiatives", metrics.get("legislative_initiatives", 0))
    s_ind = _norm("independence_index", metrics.get("independence_index", 0))

    professionalism_score = (
        s_leg * WEIGHTS["professionalism"]["legislative_initiatives"] +
        s_ind * WEIGHTS["professionalism"]["independence_index"]
    )

    # ------------------------------
    # 5. Representation (derived)
    # ------------------------------
    representation_score = (influence_score + professionalism_score) / 2

    # ------------------------------
    # 6. Cohesion (derived)
    # ------------------------------
    cohesion_score = metrics.get("party_control_index", 5) * 10
    cohesion_score = max(0, min(100, cohesion_score))

    # ------------------------------
    # 7. Narrative / Communication (derived)
    # ------------------------------
    narrative_score = _norm("media_mentions_monthly", metrics.get("media_mentions_monthly", 0))

    # ------------------------------
    # 8. NEW — Momentum & Resilience
    # ------------------------------
    pos = metrics.get("media_positive_events", 0)
    neg = metrics.get("media_negative_events", 0)

    momentum_raw = pos - neg
    s_momentum = _norm("momentum_raw", momentum_raw)

    # ------------------------------
    # Pack dimensions
    # ------------------------------
    dimensions = [
        {"dimension": "Accountability & Transparency", "score": int(integrity_score)},
        {"dimension": "Governance & Institutional Strength", "score": int(governance_score)},
        {"dimension": "Assertiveness & Influence", "score": int(influence_score)},
        {"dimension": "Policy Engagement & Expertise", "score": int(professionalism_score)},
        {"dimension": "Representation & Responsiveness", "score": int(representation_score)},
        {"dimension": "Organizational & Party Cohesion", "score": int(cohesion_score)},
        {"dimension": "Narrative & Communication", "score": int(narrative_score)},
        {"dimension": "Momentum & Resilience", "score": int(s_momentum)},   # NEW
    ]

    # ------------------------------
    # Final overall score (now 8 dimensions)
    # ------------------------------
    overall = int(sum(d["score"] for d in dimensions) / len(dimensions))

    return {
        "overall_score": overall,
        "dimensions": dimensions,
    }
