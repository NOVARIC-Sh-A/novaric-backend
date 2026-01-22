from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Optional: use your Albanian-safe normalizer + static map
try:
    from etl.politician_map import normalize_name, POLITICIAN_ID_MAP_NORMALIZED
except Exception:
    normalize_name = None
    POLITICIAN_ID_MAP_NORMALIZED = {}

# Supabase client (adapt to your existing utils/supabase_client.py)
def _get_supabase():
    """
    Tries common patterns used in this codebase:
    - utils.supabase_client.supabase (a ready client)
    - utils.supabase_client.get_supabase_client() (factory)
    """
    try:
        from utils.supabase_client import supabase  # type: ignore
        return supabase
    except Exception:
        pass

    try:
        from utils.supabase_client import get_supabase_client  # type: ignore
        return get_supabase_client()
    except Exception as e:
        raise RuntimeError(
            "Supabase client not available. Ensure utils/supabase_client.py exposes "
            "`supabase` or `get_supabase_client()`."
        ) from e


router = APIRouter(tags=["politicians"])


# ============================================================
# Response models
# ============================================================

class PoliticianCard(BaseModel):
    """
    Frontend-friendly card model (VipProfile-compatible fields).
    This is what your PoliticiansPage needs.
    """
    id: str
    name: str
    imageUrl: Optional[str] = None
    category: str = Field(default="Politikë")
    shortBio: Optional[str] = None
    detailedBio: Optional[str] = None
    dynamicScore: int = 0

    # Optional fields your UI might already use
    clickCount: int = 0
    zodiacSign: Optional[str] = None


class ResolveResponse(BaseModel):
    politician_id: Optional[int] = None


# ============================================================
# Helpers
# ============================================================

def _vip_id_from_int(pid: int) -> str:
    return f"vip{pid}"

def _party_category(party: Optional[str]) -> str:
    p = (party or "").strip()
    if not p:
        return "Politikë"
    return f"Politikë ({p})"

def _fallback_short_bio(role: Optional[str], party: Optional[str]) -> str:
    role_txt = (role or "").strip()
    if role_txt:
        return role_txt
    p = (party or "").strip()
    if p:
        return f"Figurë politike në Shqipëri ({p})."
    return "Figurë politike në Shqipëri."

def _extract_pid_from_query(query: str) -> Optional[int]:
    """
    Supports:
    - vip1, VIP1, mp12 etc. -> 1, 12
    - plain digits -> int
    """
    q = (query or "").strip()
    if not q:
        return None

    m = re.search(r"(\d+)$", q)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


# ============================================================
# 1) GET /api/politicians/cards
# ============================================================

@router.get("/politicians/cards", response_model=List[PoliticianCard])
def get_politician_cards(
    include_profiles_overlay: bool = Query(
        default=True,
        description="If true, overlays fields from public.profiles when available (bio/image/category).",
    ),
    limit: int = Query(default=500, ge=1, le=5000),
):
    """
    Returns a complete list of politicians for the frontend PoliticiansPage.

    Strategy (Option A):
    - Base source of truth: public.politicians (canonical list)
    - Optional overlay: public.profiles (if exists) to reuse bio/image/category/paragon fields
      while still guaranteeing no politician is missing.
    """
    supabase = _get_supabase()

    # 1) Load politicians table
    try:
        pol_res = (
            supabase.table("politicians")
            .select("id,name,party,role,image_url")
            .order("id", desc=False)
            .limit(limit)
            .execute()
        )
        politicians = pol_res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read politicians table: {e}")

    # 2) Optional overlay from profiles table
    profiles_by_vip_id: Dict[str, Dict[str, Any]] = {}
    if include_profiles_overlay:
        try:
            # Pull only political profiles (cheap filter)
            prof_res = (
                supabase.table("profiles")
                .select("id,name,imageUrl,category,shortBio,detailedBio,dynamicScore,clickCount,zodiacSign")
                .ilike("category", "Politik%")
                .limit(limit)
                .execute()
            )
            for p in (prof_res.data or []):
                pid = str(p.get("id") or "")
                if pid:
                    profiles_by_vip_id[pid] = p
        except Exception:
            # Overlay is best-effort; do not fail the endpoint
            profiles_by_vip_id = {}

    cards: List[PoliticianCard] = []

    for row in politicians:
        pid = int(row["id"])
        vip_id = _vip_id_from_int(pid)

        # Base fields from politicians
        base_name = row.get("name") or f"Politician {pid}"
        base_party = row.get("party")
        base_role = row.get("role")
        base_img = row.get("image_url")

        # Overlay from profiles if exists
        overlay = profiles_by_vip_id.get(vip_id)

        cards.append(
            PoliticianCard(
                id=vip_id,
                name=(overlay.get("name") if overlay else base_name) or base_name,
                imageUrl=(overlay.get("imageUrl") if overlay else base_img) or base_img,
                category=(overlay.get("category") if overlay else _party_category(base_party)) or _party_category(base_party),
                shortBio=(overlay.get("shortBio") if overlay else None) or _fallback_short_bio(base_role, base_party),
                detailedBio=(overlay.get("detailedBio") if overlay else None),
                dynamicScore=int((overlay.get("dynamicScore") if overlay else 0) or 0),
                clickCount=int((overlay.get("clickCount") if overlay else 0) or 0),
                zodiacSign=(overlay.get("zodiacSign") if overlay else None),
            )
        )

    return cards


# ============================================================
# 2) GET /api/politicians/resolve?query=
# ============================================================

@router.get("/politicians/resolve", response_model=ResolveResponse)
def resolve_politician_id(
    query: str = Query(..., min_length=1, description="vipX, numeric ID, or name"),
):
    """
    Resolves a query to a numeric politician_id.

    Resolution order:
    1) vipX / trailing digits -> int
    2) static normalized map (etl/politician_map.py) if available
    3) Supabase lookup by name (ilike) in public.politicians
    """
    q = (query or "").strip()
    if not q:
        return ResolveResponse(politician_id=None)

    # 1) vipX or trailing digits
    pid = _extract_pid_from_query(q)
    if pid is not None:
        return ResolveResponse(politician_id=pid)

    # 2) static normalized map (fast, deterministic)
    if normalize_name and POLITICIAN_ID_MAP_NORMALIZED:
        n = normalize_name(q)
        pid2 = POLITICIAN_ID_MAP_NORMALIZED.get(n)
        if pid2 is not None:
            return ResolveResponse(politician_id=int(pid2))

    # 3) DB lookup by name
    supabase = _get_supabase()
    try:
        res = (
            supabase.table("politicians")
            .select("id,name")
            .ilike("name", f"%{q}%")
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if rows:
            return ResolveResponse(politician_id=int(rows[0]["id"]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resolve failed: {e}")

    return ResolveResponse(politician_id=None)
