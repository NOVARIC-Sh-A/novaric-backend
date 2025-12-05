# etl/scoring_engine.py
"""
PARAGON scoring engine:
Converts politician-level media signals into quantitative
scores ready for insertion into Supabase `paragon_scores`.
"""

from typing import Dict, Any, List
from etl.politician_map import POLITICIAN_ID_MAP, POLITICIAN_META


# ------------------------------------------------------
# Helper: normalize values into 40–95 score range
# ------------------------------------------------------
def _scale(value: float, max_value: float, floor: int = 40, ceil: int = 95) -> int:
    if max_value <= 0:
        return floor
    ratio = value / max_value
    raw = floor + ratio * (ceil - floor)
    score = int(raw)
    return max(0, min(100, score))


def _sentiment_score(pos: int, neg: int, mentions: int) -> int:
    if mentions <= 0:
        return 50
    balance = pos - neg
    sentiment_index = balance / max(1, mentions)  # -1..+1
    normalized = (sentiment_index + 1) / 2        # → 0..1
    score = int(normalized * 100)
    return max(0, min(100, score))


# ------------------------------------------------------
# MAIN ENGINE
# ------------------------------------------------------
def build_paragon_scores_from_signals(
    signals: Dict[int, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Input (signals keyed by politician_id):
    {
        1: {
            "politician_id": 1,
            "name": "Edi Rama",
            "mentions": 12,
            "positive": 5,
            "negative": 4,
            "neutral": 3,
            "media_hits": [...]
        },
        ...
    }

    Output rows ready for Supabase:
    {
        "politician_id": 1,
        "leadership": 72,
        "integrity": 55,
        "public_impact": 81,
        "overall_score": 72,
        "dimension_scores": {...},
        "signals_raw": {...},
        "last_updated": "now()"
    }
    """

    if not signals:
        return []

    # --------------------------
    # GLOBAL NORMALIZERS
    # --------------------------
    max_mentions = max(sig.get("mentions", 0) for sig in signals.values()) or 1
    max_sources = 1

    for sig in signals.values():
        hits = sig.get("media_hits", [])
        sources = {h.get("source_url", "") for h in hits if h.get("source_url")}
        max_sources = max(max_sources, len(sources))

    results: List[Dict[str, Any]] = []

    # --------------------------
    # SCORING LOOP
    # --------------------------
    for pid, sig in signals.items():

        if pid not in POLITICIAN_META:
            print(f"[Scoring] WARNING: Missing metadata for politician_id {pid}. Skipping.")
            continue

        meta = POLITICIAN_META[pid]

        mentions = sig.get("mentions", 0)
        pos = sig.get("positive", 0)
        neg = sig.get("negative", 0)
        hits = sig.get("media_hits", [])

        num_sources = len({h.get("source_url", "") for h in hits if h.get("source_url")})

        # ------------------------------
        # CORE DIMENSIONS
        # ------------------------------
        visibility_score = _scale(mentions, max_mentions)
        diversity_score = _scale(num_sources, max_sources)
        sentiment_score = _sentiment_score(pos, neg, mentions)

        # Crisis = staying visible despite negative coverage
        crisis_index = (mentions - neg) / max(1, mentions)  # 0..1
        crisis_score = _scale(crisis_index, 1.0)

        # ------------------------------
        # PARAGON MODEL MAPPING
        # ------------------------------
        dimension_scores = {
            "Narrativa & Komunikimi": {
                "score": int((visibility_score + sentiment_score) / 2),
                "peerAverage": 60,
                "commentary": "Intensiteti i shfaqjes në media dhe toni i komunikimit publik."
            },
            "Shtrirja Mediatike": {
                "score": diversity_score,
                "peerAverage": 60,
                "commentary": "Larmia e burimeve mediatike ku përmendet figura."
            },
            "Perceptimi Publik": {
                "score": sentiment_score,
                "peerAverage": 60,
                "commentary": "Raporti mes jehonës pozitive, negative dhe neutrale."
            },
            "Qëndrueshmëria në Kriza": {
                "score": crisis_score,
                "peerAverage": 60,
                "commentary": "Përfaqësimi publik në situata tensioni dhe polemike."
            }
        }

        # Map dimensions to Supabase schema
        leadership = dimension_scores["Narrativa & Komunikimi"]["score"]
        integrity = dimension_scores["Perceptimi Publik"]["score"]
        public_impact = dimension_scores["Shtrirja Mediatike"]["score"]

        overall_score = int(
            sum(d["score"] for d in dimension_scores.values()) / len(dimension_scores)
        )

        # ------------------------------
        # FINAL RECORD FOR SUPABASE
        # ------------------------------
        row = {
            "politician_id": pid,
            "leadership": leadership,
            "integrity": integrity,
            "public_impact": public_impact,
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "signals_raw": sig,       # Store raw metrics for transparency
            "last_updated": "now()"
        }

        results.append(row)

    print(f"[Scoring] Generated PARAGON scores for {len(results)} profiles")
    return results
