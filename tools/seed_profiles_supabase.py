# tools/seed_profiles_supabase.py
"""
Seed / upsert PROFILES from mock_profiles.py into Supabase public.profiles.

Windows-friendly, “plug & play”:
  1) From backend root (where mock_profiles.py lives), run:
     PS> $env:SUPABASE_URL="https://xxxx.supabase.co"
     PS> $env:SUPABASE_SERVICE_ROLE_KEY="YOUR_SERVICE_ROLE_KEY"
     PS> python tools/seed_profiles_supabase.py

Notes:
- Uses Service Role key by default (recommended) to bypass RLS for seeding.
- Adds project root to sys.path so `from mock_profiles import PROFILES` works when run from /tools.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List, Optional

from supabase import Client, create_client


# -----------------------------------------------------------------------------
# 0) Ensure imports work when running from /tools on Windows
# -----------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Optional .env loading (won't crash if python-dotenv isn't installed)
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except Exception:
    pass


# Import your dataset (this will also run hydrate_profiles_with_engine(PROFILES))
from mock_profiles import PROFILES  # noqa: E402


# -----------------------------------------------------------------------------
# 1) Supabase client
# -----------------------------------------------------------------------------
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )

    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (recommended) in environment."
        )

    return create_client(url, key)


# -----------------------------------------------------------------------------
# 2) Normalization helpers
# -----------------------------------------------------------------------------
def infer_profile_type(category: Optional[str]) -> str:
    c = (category or "").lower()
    if "politik" in c:
        return "political"
    if "media" in c:
        return "media"
    if "biznes" in c:
        return "business"
    return "other"


def extract_party_and_role(
    category: Optional[str], short_bio: Optional[str]
) -> Dict[str, Optional[str]]:
    """
    Party: try to read from category like 'Politikë (PS)'.
    Role: best-effort extraction from shortBio first clause.
    """
    party: Optional[str] = None
    role: Optional[str] = None

    if category:
        m = re.search(r"\(([^)]+)\)", category)
        if m:
            party = m.group(1).strip()

    if short_bio:
        # e.g. "Kryeministër i Shqipërisë, Kryetar i Partisë Socialiste."
        role = short_bio.split(",")[0].strip() or None

    return {"party": party, "role": role}


def _get(p: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Read first existing key from a dict."""
    for k in keys:
        if k in p and p[k] is not None:
            return p[k]
    return default


def to_profile_row(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Maps your PROFILES objects into public.profiles columns.

    Expected table columns (recommended):
      id (text pk), name (text), category (text), profile_type (text),
      party (text), role (text),
      short_bio (text), detailed_bio (text), zodiac_sign (text),
      image_url (text),
      paragon_analysis (jsonb), maragon_analysis (jsonb),
      extra (jsonb)
    """
    profile_id = str(_get(p, "id", default="")).strip()
    name = str(_get(p, "name", default="")).strip()

    category = _get(p, "category")
    short_bio = _get(p, "shortBio", "short_bio")
    detailed_bio = _get(p, "detailedBio", "detailed_bio")
    zodiac_sign = _get(p, "zodiacSign", "zodiac_sign")
    image_url = _get(p, "imageUrl", "image_url", default="") or ""

    profile_type = infer_profile_type(category)
    pr = extract_party_and_role(category, short_bio)

    paragon_analysis = _get(p, "paragonAnalysis", "paragon_analysis")
    maragon_analysis = _get(p, "maragonAnalysis", "maragon_analysis")

    # Anything not part of the stable schema goes into extra JSONB
    reserved = {
        "id",
        "name",
        "category",
        "shortBio",
        "short_bio",
        "detailedBio",
        "detailed_bio",
        "zodiacSign",
        "zodiac_sign",
        "imageUrl",
        "image_url",
        "paragonAnalysis",
        "paragon_analysis",
        "maragonAnalysis",
        "maragon_analysis",
    }
    extra = {k: v for k, v in p.items() if k not in reserved}

    return {
        "id": profile_id,
        "name": name,
        "category": category,
        "profile_type": profile_type,
        "party": pr["party"],
        "role": pr["role"],
        "short_bio": short_bio,
        "detailed_bio": detailed_bio,
        "zodiac_sign": zodiac_sign,
        "image_url": image_url,
        "paragon_analysis": paragon_analysis,
        "maragon_analysis": maragon_analysis,
        "extra": extra or {},
    }


def chunk(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


# -----------------------------------------------------------------------------
# 3) Main seeding routine
# -----------------------------------------------------------------------------
def main() -> None:
    sb = get_supabase()

    profiles: List[Dict[str, Any]] = list(PROFILES)
    rows = [to_profile_row(p) for p in profiles if _get(p, "id") and _get(p, "name")]

    table_name = os.getenv("SUPABASE_TARGET_TABLE", "profiles").strip() or "profiles"
    batch_size = int(os.getenv("SUPABASE_UPSERT_BATCH", "200"))

    total = 0
    for batch in chunk(rows, batch_size):
        try:
            sb.table(table_name).upsert(batch, on_conflict="id").execute()
            total += len(batch)
        except Exception as e:
            msg = str(e)

            # Common failure: schema mismatch (column missing)
            if "does not exist" in msg and ("column" in msg or "relation" in msg):
                raise RuntimeError(
                    f"Supabase schema mismatch while upserting into public.{table_name}.\n"
                    f"Error: {msg}\n\n"
                    f"Action:\n"
                    f"- Ensure table public.{table_name} exists and includes the columns used by this script.\n"
                    f"- Recommended: create/update public.profiles with profile_type, short_bio, detailed_bio, "
                    f"zodiac_sign, paragon_analysis (jsonb), maragon_analysis (jsonb), extra (jsonb).\n"
                ) from e

            raise

    print(f"Seed complete. Upserted {total} rows into public.{table_name}.")


if __name__ == "__main__":
    main()
