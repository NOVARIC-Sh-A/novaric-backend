import os
import json
import math
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROFILES_JSON = os.environ.get("PROFILES_JSON", "profiles_seed.json")
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "profiles")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "200"))

# Schema/table
SCHEMA = "public"  # adjust if needed


def _headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        # Prefer minimal to reduce bandwidth; change to "representation" for debugging
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def _request(method: str, path: str, body: Optional[bytes] = None, timeout: int = 60) -> Tuple[int, str]:
    url = f"{SUPABASE_URL}{path}"
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return e.code, raw


def load_profiles() -> List[Dict[str, Any]]:
    with open(PROFILES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("profiles JSON must be a list of objects")
    return data


def fetch_politicians_map() -> Dict[str, int]:
    """
    Build name -> politician_id map from public.politicians.
    This allows us to populate profiles.politician_id for political profiles.
    """
    # Pull only what we need. If your politicians table is in a different schema, adjust.
    path = f"/rest/v1/politicians?select=id,name&limit=10000"
    status, body = _request("GET", path)
    if status >= 300:
        raise RuntimeError(f"Failed to fetch politicians list ({status}): {body}")

    rows = json.loads(body) if body else []
    out: Dict[str, int] = {}
    for r in rows:
        name = (r.get("name") or "").strip()
        pid = r.get("id")
        if name and isinstance(pid, int):
            out[name] = pid
    return out


def normalize_row(p: Dict[str, Any], pol_map: Dict[str, int]) -> Dict[str, Any]:
    """
    Convert one mock profile into a DB row compatible with public.profiles.
    We always write:
      - id (text or existing type; we keep it as given)
      - payload (full JSON object)
    We also populate "view-friendly" columns used by v_politician_cards:
      - politician_id (when we can match by name)
      - profile_image_url (from imageUrl)
      - short_bio (from shortBio)
      - headline (optional: from category)
      - detailed_bio (from detailedBio)
      - political_party (best-effort extracted from category)
    """
    raw_id = str(p.get("id") or "").strip()
    if not raw_id:
        raise ValueError("Profile missing id")

    name = (p.get("name") or "").strip()
    category = (p.get("category") or "").strip()

    image_url = p.get("imageUrl") or p.get("image_url") or None
    short_bio = p.get("shortBio") or p.get("short_bio") or None
    detailed_bio = p.get("detailedBio") or p.get("detailed_bio") or None

    # Best-effort: extract party from strings like "Politikë (PS)"
    political_party: Optional[str] = None
    if "(" in category and ")" in category:
        political_party = category.split("(", 1)[1].split(")", 1)[0].strip() or None

    politician_id: Optional[int] = None
    if name in pol_map:
        politician_id = pol_map[name]

    row: Dict[str, Any] = {
        "id": raw_id,
        "payload": p,  # store full object
    }

    # Only set these if your table actually has them; if a column doesn't exist,
    # PostgREST will error. If you are unsure, comment out the fields you don't have.
    row.update(
        {
            "politician_id": politician_id,
            "profile_image_url": image_url,
            "short_bio": short_bio,
            "headline": category or None,
            "detailed_bio": detailed_bio,
            "political_party": political_party,
        }
    )

    # Remove keys with None to avoid overwriting existing values with null
    row = {k: v for k, v in row.items() if v is not None}

    return row


def upsert_batch(rows: List[Dict[str, Any]]) -> Tuple[int, str]:
    # on_conflict=id assumes "id" is UNIQUE or PRIMARY KEY
    path = f"/rest/v1/{SUPABASE_TABLE}?on_conflict=id"
    body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
    return _request("POST", path, body=body, timeout=120)


def main() -> None:
    profiles = load_profiles()

    print(f"Loaded {len(profiles)} profiles from {PROFILES_JSON}.")

    # Build politician name -> id map (for joins in v_politician_cards)
    try:
        pol_map = fetch_politicians_map()
        print(f"Fetched {len(pol_map)} politicians for name->id matching.")
    except Exception as e:
        pol_map = {}
        print(f"WARNING: could not load politicians map; politician_id will be NULL. Error: {e}")

    rows = [normalize_row(p, pol_map) for p in profiles]

    total = len(rows)
    batches = math.ceil(total / BATCH_SIZE)

    print(f"Seeding {total} profiles into {SCHEMA}.{SUPABASE_TABLE} in batches of {BATCH_SIZE}...")

    for i in range(batches):
        batch = rows[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        status, body = upsert_batch(batch)

        if status >= 300:
            print(f"[{i+1}/{batches}] ERROR {status}: {body}")
            raise SystemExit(1)

        print(f"[{i+1}/{batches}] OK ({len(batch)} rows)")
        time.sleep(0.2)

    print("Done.")


if __name__ == "__main__":
    main()
