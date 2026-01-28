# etl/scoring_engine.py

"""
PARAGON Scoring Engine

Converts unified metrics into:
- 7 PARAGON dimensions (0–100 each) [official contract]
- overall score (0–100)

Option B2 (scoring-engine defaulting):
- If metrics look "unknown/sparse" (missing or mostly zeros), substitute neutral
  defaults for selected metrics to avoid pathological low scores (e.g., 14 everywhere).
- This is quicker but less explicit than fixing upstream metrics completeness.

This implementation is defensive:
- handles missing / malformed metric values
- clamps numeric inputs into expected ranges
- avoids division-by-zero in normalization

Notes:
- Momentum is computed internally for future use, but it is NOT
  returned as a PARAGON dimension to preserve the official 7-dimension contract.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from utils.paragon_constants import PARAGON_DIMENSIONS


# ------------------------------------------------------------
# Normalization ranges for metrics (min, max)
# ------------------------------------------------------------
RANGES: Dict[str, Tuple[float, float]] = {
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
    # Event-based momentum range (-10 to +10)
    "momentum_raw": (-10, 10),
}

# ------------------------------------------------------------
# Dimension weights
# ------------------------------------------------------------
WEIGHTS: Dict[str, Dict[str, float]] = {
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
# Helpers
# =====================================================================
def _as_number(value: Any, default: float = 0.0) -> float:
    """Best-effort numeric conversion. Returns default if not convertible."""
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return float(default)


def _clamp(value: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(value, max_v))


def _is_missing_or_zero(value: Any) -> bool:
    """
    True when value is effectively "unknown" under Option B2 rules.
    We interpret None, "", and numeric 0 as potentially "unknown" in sparse rows.
    """
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    try:
        return float(value) == 0.0  # includes "0", 0, 0.0
    except Exception:
        return True


# =====================================================================
# Option B2: neutral defaulting for sparse rows
# =====================================================================
# Neutral values should sit around mid-range and produce stable ~50–70 dimension scores.
_NEUTRAL_DEFAULTS: Dict[str, Any] = {
    # integrity (inverse): keep low-to-mid so score isn't punished hard
    "scandals_flagged": 2,
    "wealth_declaration_issues": 1,

    # governance
    "public_projects_completed": 10,
    "parliamentary_attendance": 60,
    "international_meetings": 4,

    # influence
    "party_control_index": 8,
    "media_mentions_monthly": 120,
    "social_influence": 5,

    # professionalism
    "legislative_initiatives": 5,
    "independence_index": 5,

    # narrative/sentiment
    "sentiment_score": 0,

    # momentum inputs (optional)
    "media_positive_events": 0,
    "media_negative_events": 0,
}

# Metrics used by this engine (core) — if these are all 0/missing,
# the row is very likely "unknown/sparse"
_CORE_SIGNAL_KEYS = (
    "scandals_flagged",
    "wealth_declaration_issues",
    "public_projects_completed",
    "parliamentary_attendance",
    "international_meetings",
    "party_control_index",
    "media_mentions_monthly",
    "legislative_initiatives",
    "independence_index",
    "sentiment_score",
    "social_influence",
    "media_positive_events",
    "media_negative_events",
)

# How many non-missing/meaningful values are required to consider row "non-sparse"
_MIN_NONZERO_CORE = 2


def _apply_neutral_defaults_if_sparse(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    If a row is sparse (mostly zeros/missing for core keys), substitute neutral values.

    This is intentionally conservative:
    - Only triggers when the row looks like a placeholder/unknown record.
    - Avoids overwriting meaningful real zeros when the row has enough real signal.
    """
    if not isinstance(metrics, dict):
        return {}

    nonzero = 0
    for k in _CORE_SIGNAL_KEYS:
        v = metrics.get(k)
        if not _is_missing_or_zero(v):
            nonzero += 1

    if nonzero >= _MIN_NONZERO_CORE:
        return metrics  # enough signal; do not default

    # Sparse => create a shallow copy and fill missing/zero with neutral defaults
    out = dict(metrics)
    for k, neutral in _NEUTRAL_DEFAULTS.items():
        if _is_missing_or_zero(out.get(k)):
            out[k] = neutral

    return out


# =====================================================================
# NORMALIZATION FUNCTION
# =====================================================================
def _norm(key: str, value: Any, inverse: bool = False) -> float:
    """
    Normalizes a value into 0..100 given configured ranges.
    If inverse=True, returns 100 - normalized_score.
    """
    min_v, max_v = RANGES.get(key, (0.0, 1.0))
    v = _as_number(value, default=min_v)
    v = _clamp(v, min_v, max_v)

    span = max_v - min_v
    if span <= 0:
        score = 0.0
    else:
        score = ((v - min_v) / span) * 100.0

    score = 100.0 - score if inverse else score
    return _clamp(score, 0.0, 100.0)


def _order_dimensions(dims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure stable ordering and guaranteed presence of all 7 official dimensions.
    Missing dimensions are filled with a neutral score (50).

    Additional stability:
    - clamps each score into 0..100
    - tolerates duplicate names (last one wins)
    """
    by_name: Dict[str, Dict[str, Any]] = {}
    for d in dims or []:
        if not isinstance(d, dict):
            continue

        name = d.get("dimension")
        if not isinstance(name, str) or not name:
            continue

        try:
            score = int(d.get("score", 0) or 0)
        except Exception:
            score = 0

        score = max(0, min(100, score))
        by_name[name] = {"dimension": name, "score": score}

    ordered: List[Dict[str, Any]] = []
    for name in PARAGON_DIMENSIONS:
        if name in by_name:
            ordered.append(by_name[name])
        else:
            ordered.append({"dimension": name, "score": 50})

    return ordered


# =====================================================================
# CORE SCORING ENGINE
# =====================================================================
def score_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts unified metrics into:
        - 7 PARAGON dimensions (official contract)
        - overall score (0–100)

    Returns:
        {
          "overall_score": int,
          "dimensions": [{"dimension": str, "score": int}, ...],
          # optional non-contract fields:
          "momentum": {"raw": float, "score": int}
        }
    """
    # ------------------------------------------------------------
    # Option B2: neutral defaulting for sparse/unknown rows
    # ------------------------------------------------------------
    m = _apply_neutral_defaults_if_sparse(metrics or {})

    # ------------------------------
    # 1. Accountability & Transparency (Integrity)
    # ------------------------------
    s_scandals = _norm("scandals_flagged", m.get("scandals_flagged", 0), inverse=True)
    s_wealth = _norm("wealth_declaration_issues", m.get("wealth_declaration_issues", 0), inverse=True)

    integrity_score = (
        s_scandals * WEIGHTS["integrity"]["scandals_flagged"]
        + s_wealth * WEIGHTS["integrity"]["wealth_declaration_issues"]
    )

    # ------------------------------
    # 2. Governance & Institutional Strength
    # ------------------------------
    s_projects = _norm("public_projects_completed", m.get("public_projects_completed", 0))
    s_attendance = _norm("parliamentary_attendance", m.get("parliamentary_attendance", 0))
    s_intl = _norm("international_meetings", m.get("international_meetings", 0))

    governance_score = (
        s_projects * WEIGHTS["governance"]["public_projects_completed"]
        + s_attendance * WEIGHTS["governance"]["parliamentary_attendance"]
        + s_intl * WEIGHTS["governance"]["international_meetings"]
    )

    # ------------------------------
    # 3. Assertiveness & Influence
    # ------------------------------
    s_party = _norm("party_control_index", m.get("party_control_index", 0))
    s_media = _norm("media_mentions_monthly", m.get("media_mentions_monthly", 0))
    s_social = _norm("social_influence", m.get("social_influence", 0))

    influence_score = (
        s_party * WEIGHTS["influence"]["party_control_index"]
        + s_media * WEIGHTS["influence"]["media_mentions_monthly"]
        + s_social * WEIGHTS["influence"]["social_influence"]
    )

    # ------------------------------
    # 4. Policy Engagement & Expertise
    # ------------------------------
    s_leg = _norm("legislative_initiatives", m.get("legislative_initiatives", 0))
    s_ind = _norm("independence_index", m.get("independence_index", 0))

    professionalism_score = (
        s_leg * WEIGHTS["professionalism"]["legislative_initiatives"]
        + s_ind * WEIGHTS["professionalism"]["independence_index"]
    )

    # ------------------------------
    # 5. Representation & Responsiveness (derived)
    # ------------------------------
    representation_score = _clamp((influence_score + professionalism_score) / 2.0, 0.0, 100.0)

    # ------------------------------
    # 6. Organizational & Party Cohesion (derived)
    # ------------------------------
    cohesion_raw = _as_number(m.get("party_control_index", 5), default=5.0) * 10.0
    cohesion_score = _clamp(cohesion_raw, 0.0, 100.0)

    # ------------------------------
    # 7. Narrative & Communication (derived)
    # ------------------------------
    narrative_score = _norm("media_mentions_monthly", m.get("media_mentions_monthly", 0))

    # ------------------------------
    # Momentum (computed, not part of the 7-dimension contract)
    # ------------------------------
    pos = _as_number(m.get("media_positive_events", 0), default=0.0)
    neg = _as_number(m.get("media_negative_events", 0), default=0.0)
    momentum_raw = pos - neg
    momentum_score = int(_clamp(_norm("momentum_raw", momentum_raw), 0.0, 100.0))

    # ------------------------------
    # Pack dimensions (unordered initially)
    # ------------------------------
    dimensions_unordered = [
        {"dimension": "Accountability & Transparency", "score": int(_clamp(integrity_score, 0, 100))},
        {"dimension": "Governance & Institutional Strength", "score": int(_clamp(governance_score, 0, 100))},
        {"dimension": "Assertiveness & Influence", "score": int(_clamp(influence_score, 0, 100))},
        {"dimension": "Policy Engagement & Expertise", "score": int(_clamp(professionalism_score, 0, 100))},
        {"dimension": "Representation & Responsiveness", "score": int(_clamp(representation_score, 0, 100))},
        {"dimension": "Organizational & Party Cohesion", "score": int(_clamp(cohesion_score, 0, 100))},
        {"dimension": "Narrative & Communication", "score": int(_clamp(narrative_score, 0, 100))},
    ]

    # Enforce official ordering + completeness
    dimensions = _order_dimensions(dimensions_unordered)

    # ------------------------------
    # Final overall score (7-dim average)
    # ------------------------------
    overall = int(sum(d["score"] for d in dimensions) / len(dimensions)) if dimensions else 0

    return {
        "overall_score": overall,
        "dimensions": dimensions,
        "momentum": {"raw": float(momentum_raw), "score": int(momentum_score)},
    }
