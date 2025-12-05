# etl/scoring_engine.py

from typing import Dict, Any, List

from etl.politician_map import (
    POLITICIAN_ID_MAP_NORMALIZED,
    POLITICIAN_META_NORMALIZED,
    normalize_name,
)


# ------------------------------------------------------------
# Helper: scale a value to 0–100 with soft floors
# ------------------------------------------------------------
def _scale(value: float, max_value: float, floor: int = 40, ceil: int = 95) -> int:
    """
    Normalizes a value into a score range [floor, ceil].
    Used for visibility, reach, and crisis stability.
    """
    if max_value <= 0:
        return floor

    ratio = value / max_value
    raw = floor + ratio * (ceil - floor)
    score = int(raw)

    return max(0, min(100, score))


# ------------------------------------------------------------
# Compute sentiment score
# ------------------------------------------------------------
def _sentiment_score(pos: int, neg: int, mentions: int) -> int:
    """
    Convert sentiment distribution into 0–100.
    balance = (pos - neg) / mentions → [-1, +1]
    mapped into → [0, 100]
    """
    if mentions <= 0:
        return 50  # neutral baseline

    balance = (pos - neg) / max(1, mentions)
    normalized = (balance + 1) / 2  # maps [-1..1] ➞ [0..1]
    score = int(normalized * 100)

    return max(0, min(100, score))


# ------------------------------------------------------------
# Build PARAGON scores using normalized politician keys
# ------------------------------------------------------------
def build_paragon_scores_from_signals(
    signals: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:

    if not signals:
        return []

    # Compute global max values for normalization
    max_mentions = max(sig.get("mentions", 0) for sig in signals.values()) or 1
    max_sources = 1

    # Estimate diversity of media sources
    for sig in signals.values():
        hits = sig.get("media_hits", [])
        sources = {h.get("source_url") for h in hits if h.get("source_url")}
        max_sources = max(max_sources, len(sources))

    results = []

    # ------------------------------------------------------------
    # Iterate through normalized politician keys
    # ------------------------------------------------------------
    for normalized_name, sig in signals.items():

        # Must exist in master metadata — guaranteed by normalized transformer
        meta = POLITICIAN_META_NORMALIZED.get(normalized_name)
        if not meta:
            print(f"[Scoring] WARNING: Unknown normalized name '{normalized_name}'. Skipping.")
            continue

        politician_id = meta["id"]
        full_name = meta["full_name"]

        mentions = sig.get("mentions", 0)
        pos = sig.get("positive", 0)
        neg = sig.get("negative", 0)
        neu = sig.get("neutral", 0)
        hits = sig.get("media_hits", [])

        sources = {h.get("source_url") for h in hits if h.get("source_url")}
        num_sources = len(sources)

        # --------------------------------------------------------
        # PARAGON core dimensions
        # --------------------------------------------------------

        visibility_score = _scale(mentions, max_mentions)
        reach_score = _scale(num_sources, max_sources)
        sentiment_score = _sentiment_score(pos, neg, mentions)

        # Crisis stability: presence despite negative coverage
        crisis_index = (mentions - neg) / max(1, mentions)
        crisis_score = _scale(crisis_index, 1.0)

        dimension_scores = {
            "Narrativa & Komunikimi": {
                "score": int((visibility_score + sentiment_score) / 2),
                "peerAverage": 60,
                "commentary": (
                    "Vlerësim i bazuar në prezencën mediatike dhe perceptimin emocional "
                    "të formuar nga raportimet."
                ),
            },
            "Shtrirja Mediatike": {
                "score": reach_score,
                "peerAverage": 60,
                "commentary": (
                    "Sa i shpërndarë është aktori politik në platformat kryesore mediatike."
                ),
            },
            "Perceptimi Publik": {
                "score": sentiment_score,
                "peerAverage": 60,
                "commentary": (
                    "Balanca ndërmjet lajmeve pozitive, negative dhe neutrale."
                ),
            },
            "Qëndrueshmëria në Kriza": {
                "score": crisis_score,
                "peerAverage": 60,
                "commentary": (
                    "Qëndrueshmëria e figurës politike ndaj kritikave dhe "
                    "situatave të tensionuara."
                ),
            },
        }

        overall = int(
            sum(d["score"] for d in dimension_scores.values()) / len(dimension_scores)
        )

        # --------------------------------------------------------
        # Final Supabase-ready record
        # --------------------------------------------------------
        results.append(
            {
                "politician_id": politician_id,     # correct primary key
                "politician_name": full_name,       # human-readable
                "overall_score": overall,
                "dimension_scores": dimension_scores,
                "signals_raw": sig,                 # optional — keeps full trace
                "last_updated": "now()",
            }
        )

    print(f"[Scoring] Generated PARAGON scores for {len(results)} profiles")
    return results
