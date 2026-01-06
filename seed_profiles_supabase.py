import os
import json
import math
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROFILES_JSON = os.environ.get("PROFILES_JSON", "profiles_seed.json")
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "profiles")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "200"))

# If your table has NOT NULL constraints beyond "name", set these defaults accordingly.
DEFAULT_TEXT = os.environ.get("DEFAULT_TEXT", "")  # used to avoid NOT NULL failures on text columns


def _headers(prefer: str) -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": prefer,
    }


def _request(
    method: str,
    path: str,
    body: Optional[bytes] = None,
    prefer: str = "return=minimal",
    timeout: int = 60,
) -> Tuple[int, str]:
    url = f"{SUPABASE_URL}{path}"
    req = urllib.request.Request(url, data=body, headers=_headers(prefer), method=method)
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
    status, body = _request("GET", "/rest/v1/politicians?select=id,name&limit=10000", prefer="return=representation")
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


def party_from_category(category: str) -> Optional[str]:
    if not category:
        return None
    if "(" in category and ")" in category:
        v = category.split("(", 1)[1].split(")", 1)[0].strip()
        return v or None
    return None


def build_row(p: Dict[str, Any], pol_map: Dict[str, int]) -> Dict[str, Any]:
    """
    Build a single row for INSERT/UPSERT.
    IMPORTANT: Every row must have identical keys to avoid PGRST102.
    """
    profile_id = str(p.get("id") or "").strip()
    if not profile_id:
        raise ValueError("Profile missing id")

    name = (p.get("name") or "").strip()
    if not name:
        # table enforces NOT NULL name; fail early with clear message
        raise ValueError(f"Profile {profile_id} missing name in JSON payload")

    category = (p.get("category") or "").strip()
    short_bio = p.get("shortBio") or p.get("short_bio") or ""
    detailed_bio = p.get("detailedBio") or p.get("detailed_bio") or ""
    image_url = p.get("imageUrl") or p.get("image_url") or ""

    politician_id = pol_map.get(name)
    party = party_from_category(category)

    # Use DEFAULT_TEXT to avoid NOT NULL failures on these if your schema enforces them
    # (leave as None if you prefer storing NULLs and columns allow it)
    row: Dict[str, Any] = {
        "id": profile_id,
        "name": name,
        "payload": p,

        # Common “view-friendly” columns (safe even if nullable)
        "politician_id": politician_id,
        "profile_image_url": image_url or DEFAULT_TEXT,
        "short_bio": short_bio or DEFAULT_TEXT,
        "headline": category or DEFAULT_TEXT,
        "detailed_bio": detailed_bio or DEFAULT_TEXT,
        "political_party": party,
    }
    return row


def upsert_batch(batch: List[Dict[str, Any]]) -> Tuple[int, str]:
    path = f"/rest/v1/{SUPABASE_TABLE}?on_conflict=id"
    body = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    prefer = "resolution=merge-duplicates,return=minimal"
    return _request("POST", path, body=body, prefer=prefer, timeout=120)


def main() -> None:
    profiles = load_profiles()
    print(f"Loaded {len(profiles)} profiles from {PROFILES_JSON}.")

    pol_map = fetch_politicians_map()
    print(f"Fetched {len(pol_map)} politicians for name->id matching.")

    rows = [build_row(p, pol_map) for p in profiles]

    total = len(rows)
    batches = math.ceil(total / BATCH_SIZE)
    print(f"Seeding {total} profiles into public.{SUPABASE_TABLE} in batches of {BATCH_SIZE}...")

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
