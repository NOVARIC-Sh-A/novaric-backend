# etl/metrics_contract.py
"""
Metrics Contract (Single Source of Truth)

This module is the only place where naming translations are allowed.
All ETL runners must use this module to convert:
- scraper payload -> canonical
- canonical -> DB row for paragon_metrics
- DB row -> canonical for scoring
"""

from __future__ import annotations

from typing import Any, Dict

# ---------------------------------------------------------------------
# A) Scraper output -> Canonical keys
# ---------------------------------------------------------------------
# media_scraper.py returns:
# - mentions
# - positive_events
# - negative_events
# - scandals_flagged
# - sentiment_score (float)
SCRAPER_MEDIA_TO_CANONICAL: Dict[str, str] = {
    "mentions": "media_mentions_monthly",
    "positive_events": "media_positive_events",
    "negative_events": "media_negative_events",
    "scandals_flagged": "scandals_flagged",
    "sentiment_score": "sentiment_score",
}

# ---------------------------------------------------------------------
# B) Canonical keys -> DB columns (paragon_metrics)
# ---------------------------------------------------------------------
# Based on your Supabase table columns:
# politician_id (PK)
# scandals_flag, wealth_declar, public_projec, parliamentary, international_,
# party_control_, media_mentic, legislative_ini, independence,
# media_positiv, media_negati, updated_at, sentiment_sc
CANONICAL_TO_DB_PARAGON_METRICS: Dict[str, str] = {
    "scandals_flagged": "scandals_flag",
    "wealth_declaration_issues": "wealth_declar",
    "public_projects_completed": "public_projec",
    "parliamentary_attendance": "parliamentary",
    "international_meetings": "international_",
    "party_control_index": "party_control_",
    "media_mentions_monthly": "media_mentic",
    "legislative_initiatives": "legislative_ini",
    "independence_index": "independence",
    "media_positive_events": "media_positiv",
    "media_negative_events": "media_negati",
    "sentiment_score": "sentiment_sc",
}

DB_TO_CANONICAL_PARAGON_METRICS: Dict[str, str] = {
    db_col: canon_key for canon_key, db_col in CANONICAL_TO_DB_PARAGON_METRICS.items()
}

# ---------------------------------------------------------------------
# C) Type/scale normalization helpers
# ---------------------------------------------------------------------
def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)

def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(x))
    except Exception:
        return int(default)

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def _sentiment_float_to_int(v: Any) -> int:
    """
    Canonical sentiment_score is float [-1, 1].
    DB sentiment_sc is int4 storing scaled [-100, 100].
    """
    f = _as_float(v, 0.0)
    f = _clamp(f, -1.0, 1.0)
    return int(round(f * 100.0))

def _sentiment_int_to_float(v: Any) -> float:
    """
    DB sentiment_sc is int4 [-100, 100].
    Canonical sentiment_score is float [-1, 1].
    """
    i = _as_int(v, 0)
    i = int(_clamp(i, -100, 100))
    return float(i) / 100.0

# ---------------------------------------------------------------------
# D) Translation helpers
# ---------------------------------------------------------------------
def scraper_to_canonical(payload: Dict[str, Any], mapping: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Convert a scraper payload to canonical keys.
    Unknown keys are preserved as-is.
    """
    m = mapping or SCRAPER_MEDIA_TO_CANONICAL
    out: Dict[str, Any] = {}
    for k, v in (payload or {}).items():
        out[m.get(k, k)] = v
    return out

def canonical_to_db_paragon_metrics(canonical: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert canonical metrics into a DB row (paragon_metrics columns).
    Only mapped canonical keys are emitted.

    Also applies scaling for sentiment_score -> sentiment_sc.
    """
    out: Dict[str, Any] = {}
    for canon_key, value in (canonical or {}).items():
        db_col = CANONICAL_TO_DB_PARAGON_METRICS.get(canon_key)
        if not db_col:
            continue

        if canon_key == "sentiment_score":
            out[db_col] = _sentiment_float_to_int(value)
        else:
            out[db_col] = value

    return out

def db_paragon_metrics_to_canonical(db_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a DB row from paragon_metrics into canonical keys.
    Unmapped columns are preserved as-is.

    Also applies scaling for sentiment_sc -> sentiment_score.
    """
    out: Dict[str, Any] = {}
    for db_col, value in (db_row or {}).items():
        canon_key = DB_TO_CANONICAL_PARAGON_METRICS.get(db_col, db_col)

        if canon_key == "sentiment_score":
            out[canon_key] = _sentiment_int_to_float(value)
        else:
            out[canon_key] = value

    return out
