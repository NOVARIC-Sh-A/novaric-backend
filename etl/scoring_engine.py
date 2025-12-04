# etl/scoring_engine.py
from typing import Dict, Any, List
from mock_profiles import PROFILES as MOCK_PROFILES


# ----------------------------------------
# Helper: normalize scores to 0–100 range
# ----------------------------------------
def _scale(value: float, max_value: float, floor: int = 40, ceil: int = 95) -> int:
    """
    Scale 0..max_value into [floor, ceil].
    Guarantees values are within 0..100 and avoids super low extremes.
    """
    if max_value <= 0:
        return 0

    ratio = value / max_value
    raw = floor + ratio * (ceil - floor)
    score = int(raw)

    return max(0, min(100, score))


def _sentiment_score(pos: int, neg: int, mentions: int) -> int:
    """
    Convert positive/negative balance into 0–100 sentiment score.
    sentiment_index ≈ -1 (very negative) → +1 (very positive)
    """
    if mentions <= 0:
        return 50  # neutral baseline

    balance = pos - neg
    sentiment_index = balance / max(1, mentions)  # ≈ -1..+1

    # Map [-1, 1] → [0, 100]
    normalized = (sentiment_index + 1) / 2
    score = int(normalized * 100)
    return max(0, min(100, score))


# ----------------------------------------
# Build name → profile_id mapping
# ----------------------------------------
_NAME_TO_PROFILE: Dict[str, Dict[str, Any]] = {
    p["name"]: p for p in MOCK_PROFILES if "name" in p
}


def build_paragon_scores_from_signals(
    signals: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Transform media signals into PARAGON-style score records ready for Supabase.

    Input (signals):
      {
        "Edi Rama": {
            "mentions": 7,
            "positive": 2,
            "negative": 3,
            "neutral": 2,
            "media_hits": [...]
        },
        ...
      }

    Output (each record):
      {
        "profile_id": "vip1",
        "profile_name": "Edi Rama",
        "overall_score": 78,
        "dimension_scores": {
            "Narrativa & Komunikimi": { "score": 80, "peerAverage": 60, "commentary": "..." },
            "Shtrirja Mediatike": { ... },
            "Perceptimi Publik": { ... },
            "Qëndrueshmëria në Kriza": { ... },
        },
        "last_updated": "now()"
      }
    """

    if not signals:
        return []

    # Global maxes for normalization
    max_mentions = max(sig.get("mentions", 0) for sig in signals.values()) or 1
    max_sources = 1

    # estimate unique source diversity
    for sig in signals.values():
        hits = sig.get("media_hits", [])
        sources = {h.get("source_url", "") for h in hits if h.get("source_url")}
        max_sources = max(max_sources, len(sources))

    records: List[Dict[str, Any]] = []

    for name, sig in signals.items():
        # Map to profile metadata
        profile = _NAME_TO_PROFILE.get(name)
        if not profile:
            # Politician name present in signals but not in mock_profiles
            print(f"[Scoring] WARNING: No profile found for '{name}', skipping.")
            continue

        mentions = sig.get("mentions", 0)
        pos = sig.get("positive", 0)
        neg = sig.get("negative", 0)
        neu = sig.get("neutral", 0)
        hits = sig.get("media_hits", [])

        sources = {h.get("source_url", "") for h in hits if h.get("source_url")}
        num_sources = len(sources)

        # Core derivatives
        vis_score = _scale(mentions, max_mentions)             # visibility based on mentions
        reach_score = _scale(num_sources, max_sources)         # diversity of media
        sent_score = _sentiment_score(pos, neg, mentions)      # public perception
        # crisis = more negative coverage but still present = resilience
        crisis_index = (mentions - neg) / max(1, mentions)     # 0..1: more negative → lower
        crisis_score = _scale(crisis_index, 1.0)               # normalized

        # PARAGON dimensions (you can refine names later)
        dimension_scores = {
            "Narrativa & Komunikimi": {
                "score": int((vis_score + sent_score) / 2),
                "peerAverage": 60,
                "commentary": "Vlerësim i bazuar në intensitetin e raportimeve dhe tonin publik në media.",
            },
            "Shtrirja Mediatike": {
                "score": reach_score,
                "peerAverage": 60,
                "commentary": "Numri dhe larmia e burimeve ku aktori politik shfaqet rregullisht.",
            },
            "Perceptimi Publik": {
                "score": sent_score,
                "peerAverage": 60,
                "commentary": "Balanca mes lajmeve pozitive dhe negative në hapësirën mediatike.",
            },
            "Qëndrueshmëria në Kriza": {
                "score": crisis_score,
                "peerAverage": 60,
                "commentary": "Sa i pranishëm mbetet aktori politik edhe në situata kritike dhe krizash.",
            },
        }

        overall = int(
            sum(d["score"] for d in dimension_scores.values()) / len(dimension_scores)
        )

        record = {
            "profile_id": profile["id"],
            "profile_name": profile["name"],
            "overall_score": overall,
            "dimension_scores": dimension_scores,
            "last_updated": "now()",
        }

        records.append(record)

    print(f"[Scoring] Generated PARAGON scores for {len(records)} profiles")
    return records
