# etl/evidence/politician_matcher.py
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Any

from etl.politician_map import normalize_name, POLITICIAN_ID_MAP_NORMALIZED
from utils.supabase_client import _get


# =============================================================================
# Config
# =============================================================================

_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ž0-9çë]+", re.UNICODE)

_STOPWORDS: Set[str] = {
    "dhe", "ose", "me", "pa", "nga", "te", "tek", "ne", "në", "per", "për",
    "si", "qe", "që", "se", "ka", "kishte", "janë", "është", "u", "do", "më",
    "i", "e", "të", "së", "nuk", "po",
    "the", "and", "or", "to", "in", "on", "of", "for", "with",
}

_MIN_TOKEN_LEN = 4

_ALIAS_CACHE_TTL_SECONDS = int(os.getenv("ALIAS_CACHE_TTL_SECONDS", "600"))
_MATCHER_DEBUG = (os.getenv("MATCHER_DEBUG", "").strip().lower() in {"1", "true", "yes", "y"})


# =============================================================================
# Data structures
# =============================================================================

@dataclass(frozen=True)
class MatchDebug:
    politician_id: Optional[int]
    method: str
    confidence: float
    evidence: Dict[str, Any]


# =============================================================================
# Caches (process memory)
# =============================================================================

_cached_alias_map: Optional[Dict[str, int]] = None
_cached_alias_loaded_at: float = 0.0

_cached_lastname_map: Optional[Dict[str, List[int]]] = None
_cached_pid_to_normname: Optional[Dict[int, str]] = None


# =============================================================================
# Helpers
# =============================================================================

def _tokenize(text: str) -> List[str]:
    tokens = [t.lower() for t in _TOKEN_RE.findall(text or "")]
    return [t for t in tokens if len(t) >= _MIN_TOKEN_LEN and t not in _STOPWORDS]


def _log(msg: str) -> None:
    if _MATCHER_DEBUG:
        print(f"[politician_matcher] {msg}")


def _build_pid_to_normname() -> Dict[int, str]:
    global _cached_pid_to_normname
    if _cached_pid_to_normname is not None:
        return _cached_pid_to_normname

    out: Dict[int, str] = {}
    for norm_full_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        try:
            out[int(pid)] = norm_full_name
        except Exception:
            continue

    _cached_pid_to_normname = out
    return out


def _load_alias_map() -> Dict[str, int]:
    """
    TTL-cached alias map from Supabase:
      politician_aliases(alias_normalized -> politician_id)
    """
    global _cached_alias_map, _cached_alias_loaded_at

    now = time.time()
    if _cached_alias_map is not None and (now - _cached_alias_loaded_at) < _ALIAS_CACHE_TTL_SECONDS:
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
            if isinstance(alias_n, str) and alias_n.strip():
                try:
                    out[alias_n.strip()] = int(pid)
                except Exception:
                    continue

        _cached_alias_map = out
        _cached_alias_loaded_at = now
        _log(f"aliases_loaded count={len(out)} ttl={_ALIAS_CACHE_TTL_SECONDS}s")

    except Exception as e:
        # Do not break matching if DB is unavailable.
        _log(f"alias_load_failed err={e}")
        _cached_alias_map = {}
        _cached_alias_loaded_at = now

    return _cached_alias_map or {}


def _build_lastname_map() -> Dict[str, List[int]]:
    """
    last-name token -> [politician_id, ...]
    """
    global _cached_lastname_map
    if _cached_lastname_map is not None:
        return _cached_lastname_map

    last_map: Dict[str, List[int]] = {}
    for norm_full_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        parts = [p for p in (norm_full_name or "").split() if p]
        if not parts:
            continue
        last = parts[-1]
        if len(last) < _MIN_TOKEN_LEN or last in _STOPWORDS:
            continue
        try:
            last_map.setdefault(last, []).append(int(pid))
        except Exception:
            continue

    _cached_lastname_map = last_map
    return last_map


def _best_lastname_disambiguation(
    candidates: Dict[int, int],
    tokens: Set[str],
) -> Tuple[Optional[int], int]:
    """
    Returns (best_pid, best_score).
    best_score uses:
      base hits + 3 if first-name token also present
    """
    pid_to_norm = _build_pid_to_normname()

    best_pid: Optional[int] = None
    best_score = -1

    for pid, hits in candidates.items():
        score = int(hits)
        norm_full = pid_to_norm.get(int(pid))
        if norm_full:
            parts = [x for x in norm_full.split() if x]
            if parts:
                first = parts[0]
                if first in tokens:
                    score += 3

        if score > best_score:
            best_score = score
            best_pid = int(pid)

    return best_pid, best_score


# =============================================================================
# Public APIs
# =============================================================================

def match_politician_debug(text: str) -> MatchDebug:
    """
    Debuggable version of the matcher.
    Non-breaking: you can call this from pipelines when you want diagnostics.
    """
    t_norm = normalize_name(text or "")
    if not t_norm:
        return MatchDebug(None, "empty", 0.0, {"reason": "empty_text"})

    # 1) Full-name match
    for norm_name, pid in POLITICIAN_ID_MAP_NORMALIZED.items():
        if norm_name and norm_name in t_norm:
            return MatchDebug(int(pid), "full_name", 0.98, {"matched": norm_name})

    # 2) Alias match (TTL cached)
    alias_map = _load_alias_map()
    if alias_map:
        for alias_norm, pid in alias_map.items():
            if alias_norm and alias_norm in t_norm:
                return MatchDebug(int(pid), "alias", 0.93, {"matched": alias_norm})

    # 3) Last-name match with guardrails
    tokens = set(_tokenize(t_norm))
    if not tokens:
        return MatchDebug(None, "no_tokens", 0.0, {"reason": "no_tokens"})

    last_map = _build_lastname_map()

    candidates: Dict[int, int] = {}
    for tok in tokens:
        pids = last_map.get(tok)
        if not pids:
            continue
        for pid in pids:
            candidates[int(pid)] = candidates.get(int(pid), 0) + 1

    if not candidates:
        return MatchDebug(None, "no_match", 0.0, {"tokens": sorted(tokens)[:20]})

    if len(candidates) == 1:
        pid = next(iter(candidates.keys()))
        return MatchDebug(int(pid), "last_name_unique", 0.70, {"candidates": candidates})

    best_pid, best_score = _best_lastname_disambiguation(candidates, tokens)

    # Guardrail threshold for ambiguous cases
    if best_pid is not None and best_score >= 4:
        # Confidence is heuristic; ensure it stays < alias/full-name
        conf = min(0.80, 0.55 + (best_score * 0.05))
        return MatchDebug(int(best_pid), "last_name_disambiguated", conf, {"candidates": candidates, "best_score": best_score})

    return MatchDebug(None, "ambiguous_low_conf", 0.0, {"candidates": candidates, "best_score": best_score})


def match_politician_id(text: str) -> Optional[int]:
    """
    Backward compatible API used by your pipelines.
    """
    return match_politician_debug(text).politician_id
