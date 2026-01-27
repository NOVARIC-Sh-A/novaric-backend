# etl/scoring_engine.py

from __future__ import annotations

from typing import Any, Dict, List

from utils.paragon_constants import PARAGON_DIMENSIONS


# ------------------------------------------------------------
# Normalization ranges for metrics (min, max)
# ------------------------------------------------------------
RANGES: Dict[str, tuple[float, float]] = {
    "scandals_flagged": (0, 10),            # inverse (0 is GOOD / meaningful)
    "wealth_declaration_issues": (0, 5),    # inverse (0 is GOOD / meaningful)
    "public_projects_completed": (0, 50),
    "parliamentary_attendance": (0, 100),
    "international_meetings": (0, 30),
    "party_control_index": (0, 20),
    "media_mentions_monthly": (0, 2000),
    "legislative_initiatives": (0, 20),
    "independence_index": (0, 10),
    "sentiment_score": (-1, 1),
    "social_influence": (0, 10),
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
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)  # type: ignore[arg-type]
    except Exception:
        return float(default)


def _clamp(value: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(value, max_v))


def _norm(key: str, value: Any, inverse: bool = False) -> float:
    """
    Normalizes a value into 0..100 using configured ranges.
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
    Stable ordering and guaranteed presence of all 7 official dimensions.
    Missing dims filled with neutral 50.
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
        ordered.append(by_name.get(name, {"dimension": name, "score": 50}))
    return ordered


# =====================================================================
# Option B2: "unknown -> neutral" substitutions (per-metric policy)
# =====================================================================

# Metrics where 0 usually means "not collected / unknown" in your current pipeline.
# We treat 0 (or missing) as unknown and substitute neutral defaults.
UNKNOWN_IF_ZERO_DEFAULTS: Dict[str, Any] = {
    # Governance/activity proxies
    "public_projects_completed": 5,      # modest baseline
    "parliamentary_attendance": 50,      # neutral attendance
    "international_meetings": 2,         # modest baseline

    # Influence/narrative proxies
    "media_mentions_monthly": 150,       # modest baseline; avoids narrative=0
    "party_control_index": 5,            # modest baseline
    "social_influence": 3,               # modest baseline

    # Policy/professionalism proxies
    "legislative_initiatives": 2,        # modest baseline
    "independence_index": 5,             # neutral baseline
}

# Metrics where 0 is meaningful and MUST NOT be overridden
# (especially inverse metrics where 0 means good).
NEVER_OVERRIDE_ZERO = {
    "scandals_flagged",
    "wealth_declaration_issues",
    "media_positive_events",
    "media_negative_events",
    "sentiment_score",  # 0 is neutral sentiment; treat as meaningful
}


def _metric(metrics: Dict[str, Any], key: str, default: Any = 0) -> Any:
    """
    Fetch metric with Option B2 behavior:
    - if key is in UNKNOWN_IF_ZERO_DEFAULTS and value is missing/0 -> substitute neutral default
    - if key is in NEVER_OVERRIDE_ZERO -> keep the value as-is (0 is meaningful)
    """
    if not isinstance(metrics, dict):
        metrics = {}

    raw = metrics.get(key, None)

    # Missing -> neutral for the "unknown if zero" group
    if raw is None:
        if key in UNKNOWN_IF_ZERO_DEFAULTS:
            return UNKNOWN_IF_ZERO_DEFAULTS[key]
        return default

    # Convert to numeric if possible (for zero check)
    n = _as_number(raw, default=0.0)

    # Never override 0 for these keys
    if key in NEVER_OVERRIDE_ZERO:
        return raw

    # If configured: treat 0 as unknown
    if key in UNKNOWN_IF_ZERO_DEFAULTS and abs(n) <= 0.0:
        return UNKNOWN_IF_ZERO_DEFAULTS[key]

    return raw


# =====================================================================
# CORE SCORING ENGINE
# =====================================================================
def score_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts unified metrics into:
      - 7 PARAGON dimensions (official contract)
      - overall score (0–100)
    """

    # ------------------------------
    # 1) Accountability & Transparency (Integrity)
    # 0 is meaningful here; do NOT substitute.
    # ------------------------------
    s_scandals = _norm("scandals_flagged", _metric(metrics, "scandals_flagged", 0), inverse=True)
    s_wealth = _norm("wealth_declaration_issues", _metric(metrics, "wealth_declaration_issues", 0), inverse=True)

    integrity_score = (
        s_scandals * WEIGHTS["integrity"]["scandals_flagged"]
        + s_wealth * WEIGHTS["integrity"]["wealth_declaration_issues"]
    )

    # ------------------------------
    # 2) Governance & Institutional Strength
    # Substitute neutral defaults if 0/missing (unknown).
    # ------------------------------
    s_projects = _norm("public_projects_completed", _metric(metrics, "public_projects_completed", 0))
    s_attendance = _norm("parliamentary_attendance", _metric(metrics, "parliamentary_attendance", 0))
    s_intl = _norm("international_meetings", _metric(metrics, "international_meetings", 0))

    governance_score = (
        s_projects * WEIGHTS["governance"]["public_projects_completed"]
        + s_attendance * WEIGHTS["governance"]["parliamentary_attendance"]
        + s_intl * WEIGHTS["governance"]["international_meetings"]
    )

    # ------------------------------
    # 3) Assertiveness & Influence
    # Substitute neutral defaults if 0/missing (unknown).
    # ------------------------------
    s_party = _norm("party_control_index", _metric(metrics, "party_control_index", 0))
    s_media = _norm("media_mentions_monthly", _metric(metrics, "media_mentions_monthly", 0))
    s_social = _norm("social_influence", _metric(metrics, "social_influence", 0))

    influence_score = (
        s_party * WEIGHTS["influence"]["party_control_index"]
        + s_media * WEIGHTS["influence"]["media_mentions_monthly"]
        + s_social * WEIGHTS["influence"]["social_influence"]
    )

    # ------------------------------
    # 4) Policy Engagement & Expertise
    # Substitute neutral defaults if 0/missing (unknown).
    # ------------------------------
    s_leg = _norm("legislative_initiatives", _metric(metrics, "legislative_initiatives", 0))
    s_ind = _norm("independence_index", _metric(metrics, "independence_index", 0))

    professionalism_score = (
        s_leg * WEIGHTS["professionalism"]["legislative_initiatives"]
        + s_ind * WEIGHTS["professionalism"]["independence_index"]
    )

    # ------------------------------
    # 5) Representation & Responsiveness (derived)
    # ------------------------------
    representation_score = _clamp((influence_score + professionalism_score) / 2.0, 0.0, 100.0)

    # ------------------------------
    # 6) Organizational & Party Cohesion (derived)
    # Uses party_control_index; already defaulted above.
    # ------------------------------
    cohesion_raw = _as_number(_metric(metrics, "party_control_index", 5), default=5.0) * 10.0
    cohesion_score = _clamp(cohesion_raw, 0.0, 100.0)

    # ------------------------------
    # 7) Narrative & Communication (derived)
    # Uses media_mentions_monthly; already defaulted above.
    # ------------------------------
    narrative_score = _norm("media_mentions_monthly", _metric(metrics, "media_mentions_monthly", 0))

    # ------------------------------
    # Momentum (computed; not part of 7-dim contract)
    # 0 is meaningful; do not override.
    # ------------------------------
    pos = _as_number(_metric(metrics, "media_positive_events", 0), default=0.0)
    neg = _as_number(_metric(metrics, "media_negative_events", 0), default=0.0)
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

    dimensions = _order_dimensions(dimensions_unordered)
    overall = int(sum(d["score"] for d in dimensions) / len(dimensions)) if dimensions else 0

    return {
        "overall_score": overall,
        "dimensions": dimensions,
        "momentum": {"raw": float(momentum_raw), "score": int(momentum_score)},
    }
