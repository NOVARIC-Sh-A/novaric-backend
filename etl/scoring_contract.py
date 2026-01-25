# etl/scoring_contract.py
"""
PARAGON Scoring Contract (DB ↔ Engine alignment)

This module defines the ONLY allowed mapping between:
- scoring_engine output
- paragon_scores database columns

All scoring ETL must use this.
"""

from __future__ import annotations
from typing import Any, Dict, List

# ---------------------------------------------------------------------
# A) Canonical scoring output keys (from scoring_engine.score_metrics)
# ---------------------------------------------------------------------
CANONICAL_SCORE_KEYS = {
    "overall_score",
    "dimensions",
    "momentum",
}

# ---------------------------------------------------------------------
# B) Canonical → DB column mapping (paragon_scores)
# ---------------------------------------------------------------------
CANONICAL_TO_DB_PARAGON_SCORES: Dict[str, str] = {
    "overall_score": "overall_score",
    "dimensions": "dimension_scores",   # ✅ correct column
    "signals_raw": "signals_raw",
}

# ---------------------------------------------------------------------
# C) Dimension list → compact numeric map (optional legacy fields)
# ---------------------------------------------------------------------
def dimensions_to_numeric_map(dimensions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Converts:
      [{"dimension": "...", "score": 72}, ...]
    into:
      {"Accountability & Transparency": 72, ...}
    """
    out: Dict[str, int] = {}
    for d in dimensions or []:
        name = d.get("dimension")
        score = d.get("score")
        if isinstance(name, str) and isinstance(score, int):
            out[name] = score
    return out

# ---------------------------------------------------------------------
# D) Canonical → DB row builder
# ---------------------------------------------------------------------
def canonical_score_to_db_row(
    politician_id: int,
    canonical_score: Dict[str, Any],
    *,
    signals_raw: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build a paragon_scores DB row from canonical scoring output.
    """

    row: Dict[str, Any] = {
        "politician_id": politician_id,
    }

    if "overall_score" in canonical_score:
        row["overall_score"] = int(canonical_score["overall_score"])

    if "dimensions" in canonical_score:
        dims = canonical_score["dimensions"]
        row["dimension_scores"] = dims
        row["dimensions_json"] = dims  # kept for backward compatibility

    if signals_raw is not None:
        row["signals_raw"] = signals_raw

    return row
