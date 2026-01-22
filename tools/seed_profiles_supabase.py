import os
import re
from typing import Any, Dict, List, Optional

from supabase import create_client, Client

# Import your dataset (this will also run hydrate_profiles_with_engine(PROFILES))
from mock_profiles import PROFILES  # noqa: F401


def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (recommended) in env."
        )
    return create_client(url, key)


def infer_profile_type(category: Optional[str]) -> str:
    c = (category or "").lower()
    if "politik" in c:
        return "political"
    if "media" in c:
        return "media"
    if "biznes" in c:
        return "business"
    return "other"


def extract_party_and_role(category: Optional[str], short_bio: Optional[str]) -> Dict[str, Optional[str]]:
    """
    Party: try to read from category like 'Politikë (PS)' or from known patterns.
    Role: best-effort extraction from shortBio first sentence (optional).
    """
    party = None
    role = None

    if category:
        m = re.search(r"\(([^)]+)\)", category)
        if m:
            party = m.group(1).strip()

    # Very light heuristic for role (you can refine later)
    if short_bio:
        role = short_bio.split(",")[0].strip()  # e.g. "Kryeministër i Shqipërisë"

    return {"party": party, "role": role}


def to_profile_row(p: Dict[str, Any]) -> Dict[str, Any]:
    profile_id = str(p.get("id", "")).strip()
    name = str(p.get("name", "")).strip()

    category = p.get("category")
    short_bio = p.get("shortBio") or p.get("short_bio")
    detailed_bio = p.get("detailedBio") or p.get("detailed_bio")

    zodiac_sign = p.get("zodiacSign") or p.get("zodiac_sign")

    image_url = p.get("imageUrl") or p.get("image_url") or ""
    profile_type = infer_profile_type(category)

    pr = extract_party_and_role(category, short_bio)

    paragon_analysis = p.get("paragonAnalysis") or p.get("paragon_analysis")
    maragon_analysis = p.get("maragonAnalysis") or p.get("maragon_analysis")

    # Store any extra fields without schema churn (logos, audience metrics, etc.)
    reserved = {
        "id", "name",
        "category",
        "shortBio", "short_bio",
        "detailedBio", "detailed_bio",
        "zodiacSign", "zodiac_sign",
        "imageUrl", "image_url",
        "paragonAnalysis", "paragon_analysis",
        "maragonAnalysis", "maragon_analysis",
    }
    extra = {k: v for k, v in p.items() if k not in reserved}

    row = {
        "id": profile_id,
        "name": name,
        "category": category,
        "profile_type": profile_type,
        "party": pr["party"],
        "role": pr["role"],

        "short_bio": short_bio,
        "detailed_bio": detailed_bio,
        "zodiac_sign": zodiac_sign,

        # keep both columns aligned
        "image_url": image_url,
        "profile_image_url": image_url,

        "paragon_analysis": paragon_analysis,
        "maragon_analysis": maragon_analysis,

        "extra": extra or {},
    }
    return row


def chunk(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def main() -> None:
    sb = get_supabase()

    profiles: List[Dict[str, Any]] = list(PROFILES)  # imported from mock_profiles.py
    rows = [to_profile_row(p) for p in profiles if p.get("id") and p.get("name")]

    batch_size = int(os.getenv("SUPABASE_UPSERT_BATCH", "200"))

    total = 0
    for batch in chunk(rows, batch_size):
        resp = (
            sb.table("profiles")
            .upsert(batch, on_conflict="id")
            .execute()
        )
        # Supabase python client returns data in resp.data; we don't rely on it here
        total += len(batch)

    print(f"Seed complete. Upserted {total} rows into public.profiles.")


if __name__ == "__main__":
    main()
