# etl/transformer.py
import re
import unicodedata
from typing import List, Dict, Any

POLITICIANS = [
    "Edi Rama",
    "Sali Berisha",
    "Ilir Meta",
    "Lulzim Basha",
    "Monika Kryemadhi",
    "Erion Veliaj",
    "Belind Këlliçi",
    "Bajram Begaj",
    "Benet Beci",
    "Nard Ndoka",
]

# Precompute normalized names for matching
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text.lower()

NORMALIZED_MAP = {
    p: {
        "full": normalize(p),
        "first": normalize(p.split()[0]),
        "last": normalize(p.split()[-1]),
    }
    for p in POLITICIANS
}


def match_politician(text: str) -> str | None:
    """
    Attempt to match article text against politician names:
    - Full name match
    - First name match
    - Last name match
    - Case & diacritic insensitive
    """
    norm = normalize(text)

    for p, parts in NORMALIZED_MAP.items():
        if parts["full"] in norm:
            return p
        if parts["first"] in norm:
            return p
        if parts["last"] in norm:
            return p

    return None


def build_signals(articles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert raw scraped articles into PARAGON input signals.
    """
    signals = {}

    for item in articles:
        title = item.get("title", "")
        matched = match_politician(title)

        if not matched:
            continue

        if matched not in signals:
            signals[matched] = {
                "mentions": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "media_hits": [],
            }

        signals[matched]["mentions"] += 1
        signals[matched]["media_hits"].append(item)

        # VERY simple sentiment placeholder
        t = title.lower()
        if any(w in t for w in ["kritikon", "akuza", "skandal", "debate"]):
            signals[matched]["negative"] += 1
        elif any(w in t for w in ["lavdëron", "mbështet", "fitore"]):
            signals[matched]["positive"] += 1
        else:
            signals[matched]["neutral"] += 1

    return signals
