from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.supabase_client import supabase  # adjust import if your client is elsewhere


def _safe_str(x: Any) -> Optional[str]:
    return None if x is None else str(x)


def get_politician_cards(limit: int = 500, q: str | None = None) -> List[Dict[str, Any]]:
    """
    Returns a normalized list of politician cards for the PoliticiansPage.

    Source of truth: public.politicians
    Optional enrichment: public.profiles (if matching exists)
    """

    # 1) Fetch politicians (source of truth)
    pol_query = supabase.table("politicians").select(
        "id,name,party,role,image_url,slug"
    ).limit(limit)

    if q:
        # Supabase ilike uses %...%
        pol_query = pol_query.ilike("name", f"%{q}%")

    pol_res = pol_query.execute()
    politicians = pol_res.data or []

    if not politicians:
        return []

    # 2) Fetch matching profiles (optional). We match by id.
    ids = [p["id"] for p in politicians if p.get("id") is not None]

    profiles_by_id: Dict[int, Dict[str, Any]] = {}
    if ids:
        prof_res = (
            supabase.table("profiles")
            .select("id,name,category,shortBio,imageUrl,paragonAnalysis,zodiacSign,dynamicScore,clickCount,audienceRating")
            .in_("id", ids)
            .execute()
        )
        for r in (prof_res.data or []):
            try:
                profiles_by_id[int(r["id"])] = r
            except Exception:
                continue

    # 3) Build cards: politician row always wins for identity; profile augments if present
    cards: List[Dict[str, Any]] = []
    for p in politicians:
        pid = int(p["id"])
        prof = profiles_by_id.get(pid)

        name = p.get("name") or (prof.get("name") if prof else None) or f"Politician {pid}"
        party = _safe_str(p.get("party")) or "IND"
        role = _safe_str(p.get("role"))

        # Prefer politicians.image_url, fallback to profiles.imageUrl
        image_url = p.get("image_url") or (prof.get("imageUrl") if prof else None)

        # For frontend compatibility with existing VipProfile type:
        # category should be "Politikë (PS)" style
        category = f"Politikë ({party})"

        card = {
            "id": pid,
            "name": name,
            "imageUrl": image_url,
            "category": category,
            "shortBio": (prof.get("shortBio") if prof else None) or (role or "Profil politik në përpunim."),
            "dynamicScore": (prof.get("dynamicScore") if prof else 0) or 0,
            "clickCount": (prof.get("clickCount") if prof else None),
            "audienceRating": (prof.get("audienceRating") if prof else None),
            # optional extras if you want to use them later
            "slug": p.get("slug"),
        }

        cards.append(card)

    return cards
