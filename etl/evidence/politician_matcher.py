# etl/evidence/politician_matcher.py
from __future__ import annotations
from typing import Optional

from etl.politician_map import normalize_name, POLITICIAN_ID_MAP_NORMALIZED

def match_politician_id(text: str) -> Optional[int]:
    """
    Conservative matcher:
    - returns first exact-name match found in the text (normalized)
    - avoids fuzzy matching in v1 (reduces false positives)
    """
    t = normalize_name(text or "")
    if not t:
        return None

    # Check for presence of canonical names as substrings
    # (safe because normalize_name lowercases and normalizes ç/ë)
    for norm_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        if norm_name and norm_name in t:
            return int(pid)
    return None
