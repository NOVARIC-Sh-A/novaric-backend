# etl/scoring_engine.py
from typing import List, Dict, Any


PARAGON_DIMENSIONS = [
    "Narrative & Communication",
    "Visibility & Reach",
    "Media Saturation",
]


def _scale(value: float, max_value: float) -> int:
    if max_value <= 0:
        return 0
    # Scale 0–max → 40–95 (avoid extreme 0 and 100)
    ratio = value / max_value
    raw = 40 + ratio * 55
    return max(0, min(100, int(raw)))


def build_paragon_scores_from_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Turn media signals into a list of DB-ready records:

    {
      profile_id,
      profile_name,
      overall_score,
      dimension_scores: {
        "Narrative & Communication": { score, peerAverage, commentary },
        ...
      }
    }
    """

    if not signals:
        return []

    max_mentions = max(s["total_mentions"] for s in signals) or 1

    records: List[Dict[str, Any]] = []

    for sig in signals:
        mentions = sig["total_mentions"]
        num_sources = len(sig.get("sources", []))

        # Very simple heuristics (you can refine these later)
        visibility_score = _scale(mentions, max_mentions)
        saturation_score = _scale(num_sources, max_sources := max(1, max(len(s["sources"]) for s in signals)))
        narrative_score = int((visibility_score + saturation_score) / 2)

        dim_scores: Dict[str, Dict[str, Any]] = {
            "Narrative & Communication": {
                "score": narrative_score,
                "peerAverage": 60,
                "commentary": "Vlerësim i gjeneruar nga prania në media dhe artikulimi publik.",
            },
            "Visibility & Reach": {
                "score": visibility_score,
                "peerAverage": 60,
                "commentary": "Sa shpesh përmendet në burime të ndryshme mediatike.",
            },
            "Media Saturation": {
                "score": saturation_score,
                "peerAverage": 60,
                "commentary": "Larmi burimesh dhe qëndrueshmëri në hapësirën mediatike.",
            },
        }

        overall_score = int(
            sum(dim["score"] for dim in dim_scores.values()) / len(dim_scores)
        )

        records.append(
            {
                "profile_id": sig["profile_id"],
                "profile_name": sig["profile_name"],
                "overall_score": overall_score,
                "dimension_scores": dim_scores,
                "last_updated": "now()",
            }
        )

    print(f"[Scoring] Generated scores for {len(records)} profiles")
    return records
