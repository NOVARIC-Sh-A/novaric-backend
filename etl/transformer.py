# etl/transformer.py
"""
Transforms scraped media articles into aggregated politician-level signals.
Version 3: Includes full Albanian name normalization and normalized lookup.
"""

from typing import List, Dict, Any
import re
import unicodedata

from etl.politician_map import (
    POLITICIAN_META_NORMALIZED,
    POLITICIAN_ID_MAP_NORMALIZED,
    normalize_name,
)

# ------------------------------------------------------------
# Build lookup dictionaries for matching
# ------------------------------------------------------------

# ALL canonical normalized names
NORMALIZED_NAMES = list(POLITICIAN_META_NORMALIZED.keys())

# Pre-compute keyword maps for fuzzy matching
KEYWORD_MAP = {}

for canonical_norm_name in NORMALIZED_NAMES:
    meta = POLITICIAN_META_NORMALIZED[canonical_norm_name]
    full_name = meta["full_name"]

    parts = full_name.split()
    first = parts[0]
    last = parts[-1]

    KEYWORD_MAP[canonical_norm_name] = {
        "full_norm": canonical_norm_name,
        "first_norm": normalize_name(first),
        "last_norm": normalize_name(last),
        "original_full": full_name,
    }


# ------------------------------------------------------------
# Helper: Does an article mention a politician?
# ------------------------------------------------------------
def _article_mentions(article_text: str, keymap: Dict[str, str]) -> bool:
    """
    Uses normalized matching for full name, first name, and last name.
    """

    text_norm = normalize_name(article_text)

    # FULL NAME MATCH
    if keymap["full_norm"] in text_norm:
        return True

    # LAST NAME MATCH (most reliable in news)
    if re.search(rf"\b{re.escape(keymap['last_norm'])}\b", text_norm):
        return True

    # FIRST NAME MATCH – except overly common Albanian first names
    COMMON_FIRST = {"edi", "ilir", "monika", "bajram", "ardit"}

    if keymap["first_norm"] not in COMMON_FIRST:
        if re.search(rf"\b{re.escape(keymap['first_norm'])}\b", text_norm):
            return True

    return False


# ------------------------------------------------------------
# Build politician-level aggregated signals
# ------------------------------------------------------------
def build_signals(articles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Output uses *normalized politician names* as keys.
    Example:
        {
          "ilir meta" (normalized):
              {
                "politician_id": 3,
                "mentions": 7,
                "positive": 2,
                "negative": 3,
                "neutral": 2,
                "media_hits": [...]
              }
        }
    """

    signals = {
        norm_name: {
            "politician_id": POLITICIAN_ID_MAP_NORMALIZED[norm_name],
            "mentions": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "media_hits": [],
        }
        for norm_name in NORMALIZED_NAMES
    }

    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")

        combined = f"{title} {content}".strip()
        combined_norm = normalize_name(combined)

        # ----------------------------------------------------
        # SENTIMENT DETECTION (heuristic; upgraded later)
        # ----------------------------------------------------
        sentiment = "neutral"

        NEG = ["kritik", "akuz", "skandal", "përplasje", "sulm", "negativ"]
        POS = ["lavd", "mbështet", "pozitiv", "arritje", "vlerëso"]

        if any(w in combined_norm for w in NEG):
            sentiment = "negative"
        elif any(w in combined_norm for w in POS):
            sentiment = "positive"

        # ----------------------------------------------------
        # MATCH AGAINST EVERY POLITICIAN
        # ----------------------------------------------------
        for norm_name, keymap in KEYWORD_MAP.items():

            if _article_mentions(combined_norm, keymap):

                signals[norm_name]["mentions"] += 1
                signals[norm_name]["media_hits"].append(article)

                if sentiment == "positive":
                    signals[norm_name]["positive"] += 1
                elif sentiment == "negative":
                    signals[norm_name]["negative"] += 1
                else:
                    signals[norm_name]["neutral"] += 1

    # ----------------------------------------------------
    # RETURN ONLY POLITICIANS WHO APPEARED IN MEDIA
    # ----------------------------------------------------
    filtered = {
        k: v
        for k, v in signals.items()
        if v["mentions"] > 0
    }

    return filtered
