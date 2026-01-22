# routers/politicians.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Query

from etl.politician_map import (
    POLITICIAN_ID_MAP,
    POLITICIAN_ID_MAP_NORMALIZED,
    POLITICIAN_META,
    normalize_name,
)

from utils.data_loader import load_profiles_data

router = APIRouter(prefix="/politicians", tags=["politicians"])

DEFAULT_AVATAR = "https://novaric.co/wp-content/uploads/2025/11/MaleProfile.jpg"


def _as_str_id(pid: int) -> str:
    # Frontend profiles use string IDs (vip1..vip100) in many places
    return f"vip{pid}"


def _safe_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


def _build_default_card(name: str, pid: int) -> Dict[str, Any]:
    # Minimal VipProfile-like payload, compatible with PoliticiansPage filtering by category "Politikë"
    return {
        "id": _as_str_id(pid),
        "name": name,
        "imageUrl": DEFAULT_AVATAR,
        "category": "Politikë (IND)",
        "shortBio": "Profil në proces pasurimi nga NOVARIC® PARAGON Engine.",
        "detailedBio": "",
        "zodiacSign": None,
        "dynamicScore": 0,
    }


def _index_profiles_by_vip_id(profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in profiles or []:
        pid = p.get("id")
        if pid is None:
            continue
        out[str(pid)] = p
    return out


def _index_profiles_by_name(profiles: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in profiles or []:
        name = p.get("name")
        if not name:
            continue
        out[normalize_name(str(name))] = p
    return out


@router.get("/cards")
def get_politician_cards(
    include_profiles: bool = Query(default=True, description="Merge fields from loaded profiles data if available"),
) -> List[Dict[str, Any]]:
    """
    Option A:
    - Always return the canonical politician list (100).
    - Merge existing profile fields if found, but never drop missing politicians.
    """
    profiles_data: List[Dict[str, Any]] = []
    if include_profiles:
        try:
            profiles_data = load_profiles_data()
        except Exception:
            profiles_data = []

    by_vip_id = _index_profiles_by_vip_id(profiles_data)
    by_name = _index_profiles_by_name(profiles_data)

    cards: List[Dict[str, Any]] = []

    # Ensure deterministic order by politician id
    for name, pid in sorted(POLITICIAN_ID_MAP.items(), key=lambda kv: kv[1]):
        card = _build_default_card(name=name, pid=pid)

        vip_id = _as_str_id(pid)
        p = by_vip_id.get(vip_id) or by_name.get(normalize_name(name))

        if p:
            # Merge “known-good” profile fields if they exist
            # (Keep defaults if missing)
            card["id"] = str(p.get("id", card["id"]))
            card["name"] = p.get("name", card["name"])
            card["imageUrl"] = p.get("imageUrl", card["imageUrl"])
            card["category"] = p.get("category", card["category"])
            card["shortBio"] = p.get("shortBio", card["shortBio"])
            card["detailedBio"] = p.get("detailedBio", card["detailedBio"])
            card["zodiacSign"] = p.get("zodiacSign", card["zodiacSign"])
            card["dynamicScore"] = p.get("dynamicScore", card["dynamicScore"])

        cards.append(card)

    return cards


@router.get("/resolve")
def resolve_politician_id(
    query: str = Query(..., description="Name (Albanian-safe) or vipX"),
) -> Dict[str, Optional[int]]:
    """
    Returns a numeric politician_id for PARAGON recompute.

    Examples:
      - query=Edi%20Rama -> 1
      - query=vip1 -> 1
      - query=Vip100 -> 100
    """
    if not query:
        return {"politician_id": None}

    q = query.strip()

    # vipX pattern support
    import re
    m = re.search(r"vip(\d+)$", q, flags=re.IGNORECASE)
    if m:
        pid = _safe_int(m.group(1))
        return {"politician_id": pid}

    # normalized name lookup
    norm = normalize_name(q)
    pid = POLITICIAN_ID_MAP_NORMALIZED.get(norm)

    # Try a loose fallback: match against canonical names normalized
    if pid is None:
        # attempt partial match if user passes "rama" etc.
        for key, v in POLITICIAN_ID_MAP_NORMALIZED.items():
            if norm and norm in key:
                pid = v
                break

    return {"politician_id": pid}
