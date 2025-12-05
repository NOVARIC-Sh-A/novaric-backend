# etl/transformer.py
"""
Transforms scraped media articles into aggregated politician-level signals.
Version 3: Uses real politician_id mapping + fuzzy Albanian name matching.
"""

from typing import List, Dict, Any
import re
from etl.politician_map import POLITICIAN_ID_MAP


# ------------------------------------------------------
# Build name → ID + keyword maps
# ------------------------------------------------------
POLITICIANS = {
    name: {"id": POLITICIAN_ID_MAP[name], "name": name}
    for name in POLITICIAN_ID_MAP
}

KEYWORD_MAP = {}

for full_name in POLITICIANS:
    parts = full_name.split()
    first = parts[0]
    last = parts[-1]

    KEYWORD_MAP[full_name] = {
        "full": full_name.lower(),
        "first": first.lower(),
        "last": last.lower(),
    }


# ------------------------------------------------------
# Helper: check if article mentions a given politician
# ------------------------------------------------------
def _article_mentions(article_text: str, keymap: Dict[str, str]) -> bool:
    text = article_text.lower()

    # FULL name match
    if keymap["full"] in text:
        return True

    # Last name (primary disambiguator)
    if re.search(rf"\b{re.escape(keymap['last'])}\b", text):
        return True

    # First name match (skip very common Albanian names)
    if keymap["first"] not in ["edi", "ilir", "monika", "bajram", "ardit"]:
        if re.search(rf"\b{re.escape(keymap['first'])}\b", text):
            return True

    return False


# ------------------------------------------------------
# MAIN: Build politician-level signals
# ------------------------------------------------------
def build_signals(articles: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Input: raw scraped articles
    Output: signals per politician_id
    """

    # Initialize empty signals for each politician
    signals = {
        POLITICIANS[name]["id"]: {
            "politician_id": POLITICIANS[name]["id"],
            "name": name,
            "mentions": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "media_hits": [],
        }
        for name in POLITICIANS
    }

    for article in articles:
        title = article.get("title", "")
        text = article.get("content", "")

        combined = f"{title} {text}".strip().lower()

        # Basic sentiment heuristic (to be replaced by ML)
        sentiment = "neutral"
        if any(w in combined for w in ["kritik", "akuz", "skandal", "përplasje", "sulmo"]):
            sentiment = "negative"
        elif any(w in combined for w in ["lavd", "mbështet", "pozitiv", "arritje"]):
            sentiment = "positive"

        # Try matching each politician by fuzzy name rules
        for full_name, keymap in KEYWORD_MAP.items():
            if _article_mentions(combined, keymap):

                pid = POLITICIANS[full_name]["id"]

                signals[pid]["mentions"] += 1
                signals[pid]["media_hits"].append(article)

                if sentiment == "positive":
                    signals[pid]["positive"] += 1
                elif sentiment == "negative":
                    signals[pid]["negative"] += 1
                else:
                    signals[pid]["neutral"] += 1

    # Return only politicians who were actually found in articles
    filtered = {pid: v for pid, v in signals.items() if v["mentions"] > 0}

    return filtered
