# etl/evidence/politician_matcher.py
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from etl.politician_map import normalize_name, POLITICIAN_ID_MAP_NORMALIZED
from utils.supabase_client import _get


# ---------------------------------------------------------------------
# Lightweight tokenization (Albanian-safe)
# ---------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ž0-9çë]+", re.UNICODE)

# Common Albanian/English stopwords to reduce noise in token matching
_STOPWORDS: Set[str] = {
    "dhe", "ose", "me", "pa", "nga", "te", "tek", "ne", "në", "per", "për",
    "si", "qe", "që", "se", "ka", "kishte", "janë", "është", "u", "do", "më",
    "i", "e", "të", "së", "nuk", "po",
    "the", "and", "or", "to", "in", "on", "of", "for", "with",
}

# Guardrails: only consider tokens with at least this many characters
_MIN_TOKEN_LEN = 4


# ---------------------------------------------------------------------
# Cache (per process run) to avoid repeated DB calls
# ---------------------------------------------------------------------
_cached_alias_map: Optional[Dict[str, int]] = None
_cached_lastname_map: Optional[Dict[str, List[int]]] = None


def _tokenize(text: str) -> List[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    return [t for t in tokens if len(t) >= _MIN_TOKEN_LEN and t not in _STOPWORDS]


def _load_alias_map() -> Dict[str, int]:
    """
    Loads politician_aliases from Supabase, builds:
      alias_normalized -> politician_id

    If table is empty/unavailable, returns {} safely.
    """
    global _cached_alias_map
    if _cached_alias_map is not None:
        return _cached_alias_map

    out: Dict[str, int] = {}
    try:
        rows = _get(
            "politician_aliases",
            {"select": "politician_id,alias_normalized", "limit": "5000"},
        )
        for r in rows:
            pid = r.get("politician_id")
            alias_n = r.get("alias_normalized")
            if isinstance(pid, int) and isinstance(alias_n, str) and alias_n.strip():
                out[alias_n.strip()] = int(pid)
    except Exception:
        # If table doesn't exist or API fails, do not break matching.
        out = {}

    _cached_alias_map = out
    return out


def _build_lastname_map() -> Dict[str, List[int]]:
    """
    Builds a map from last-name token -> [politician_id, ...].
    We only use last-name tokens that are distinctive enough:
      - token length >= MIN
      - token not a stopword
      - token mapped to exactly one politician (unique) OR we keep list for later disambiguation
    """
    global _cached_lastname_map
    if _cached_lastname_map is not None:
        return _cached_lastname_map

    last_map: Dict[str, List[int]] = {}
    for norm_full_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        # norm_full_name is already normalized lowercase
        parts = [p for p in norm_full_name.split() if p]
        if not parts:
            continue

        last = parts[-1]
        if len(last) < _MIN_TOKEN_LEN or last in _STOPWORDS:
            continue

        last_map.setdefault(last, []).append(int(pid))

    _cached_lastname_map = last_map
    return last_map


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def match_politician_id(text: str) -> Optional[int]:
    """
    Returns a politician_id if a safe match is found, else None.

    Matching strategy (in order):
      1) Full-name substring match (exact normalized names)
      2) Alias substring match (from politician_aliases.alias_normalized)
      3) Last-name token match (only if unique last name OR disambiguated by presence of first-name token)
    """
    t_norm = normalize_name(text or "")
    if not t_norm:
        return None

    # 1) Full-name match (most reliable)
    for norm_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        if norm_name and norm_name in t_norm:
            return int(pid)

    # 2) Alias match (DB-driven; you control aliases)
    alias_map = _load_alias_map()
    if alias_map:
        for alias_norm, pid in alias_map.items():
            if alias_norm and alias_norm in t_norm:
                return int(pid)

    # 3) Last-name token match with guardrails
    tokens = set(_tokenize(t_norm))
    if not tokens:
        return None

    last_map = _build_lastname_map()

    # Candidate IDs found via last-name tokens
    candidates: Dict[int, int] = {}  # pid -> hit_count
    for tok in tokens:
        pids = last_map.get(tok)
        if not pids:
            continue
        for pid in pids:
            candidates[pid] = candidates.get(pid, 0) + 1

    if not candidates:
        return None

    # If we have a single candidate, accept it.
    if len(candidates) == 1:
        return next(iter(candidates.keys()))

    # If multiple candidates, attempt disambiguation:
    # prefer candidate whose first-name token also appears.
    # Example: if tok=spahiu matches multiple, but "bardh" appears too -> choose Bardh Spahia.
    best_pid: Optional[int] = None
    best_score = -1

    for pid, hits in candidates.items():
        # fetch the normalized full name for this pid
        # (reverse lookup is small; safe)
        full_norm = None
        for n, p in POLITICIAN_ID_MAP_NORMALIZED.items():
            if int(p) == int(pid):
                full_norm = n
                break

        score = hits
        if full_norm:
            parts = [x for x in full_norm.split() if x]
            if parts:
                first = parts[0]
                # if first-name token appears in text, boost strongly
                if first in tokens:
                    score += 3

        if score > best_score:
            best_score = score
            best_pid = pid

    # Require a minimum confidence threshold for ambiguous cases
    # (prevents random collisions on common surnames)
    if best_score >= 4 and best_pid is not None:
        return int(best_pid)

    return None
