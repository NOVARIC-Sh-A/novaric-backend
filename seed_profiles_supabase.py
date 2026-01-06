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

# Set to "1" if you want reminding columns to be populated too
ENRICH_COLUMNS = os.environ.get("ENRICH_COLUMNS", "1") == "1"


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
    # Adjust if your table name/schema differs
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


def upsert_payload_batch(batch: List[Dict[str, Any]]) -> Tuple[int, str]:
    """
    IMPORTANT: Every object in the array has the SAME keys: {id, payload}
    This avoids PGRST102.
    """
    path = f"/rest/v1/{SUPABASE_TABLE}?on_conflict=id"
    body = json.dumps(batch, ensure_ascii=False).encode("utf-8")
    prefer = "resolution=merge-duplicates,return=minimal"
    return _request("POST", path, body=body, prefer=prefer, timeout=120)


def patch_profile(profile_id: str, patch: Dict[str, Any]) -> Tuple[int, str]:
    """
    Patch a single row by id. Keys can differ between calls; no PGRST102 risk.
    """
    # URL-encode quotes around the value
    path = f"/rest/v1/{SUPABASE_TABLE}?id=eq.{urllib.parse.quote(profile_id)}"
    body = json.dumps(patch, ensure_ascii=False).encode("utf-8")
    prefer = "return=minimal"
    return _request("PATCH", path, body=body, prefer=prefer, timeout=60)


def main() -> None:
    profiles = load_profiles()
    print(f"Loaded {len(profiles)} profiles from {PROFILES_JSON}.")

    try:
        pol_map = fetch_politicians_map()
        print(f"Fetched {len(pol_map)} politicians for name->id matching.")
    except Exception as e:
        pol_map = {}
        print(f"WARNING: could not load politicians map; politician_id will be NULL. Error: {e}")

    # Step 1: upsert only (id, payload) in batches (uniform keys => no PGRST102)
    payload_rows = []
    for p in profiles:
        pid = str(p.get("id") or "").strip()
        if not pid:
            raise ValueError("Profile missing id")
        payload_rows.append({"id": pid, "payload": p})

    total = len(payload_rows)
    batches = math.ceil(total / BATCH_SIZE)
    print(f"Seeding {total} profiles into public.{SUPABASE_TABLE} (id + payload) in batches of {BATCH_SIZE}...")

    for i in range(batches):
        batch = payload_rows[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        status, body = upsert_payload_batch(batch)
        if status >= 300:
            print(f"[{i+1}/{batches}] ERROR {status}: {body}")
            raise SystemExit(1)
        print(f"[{i+1}/{batches}] OK ({len(batch)} rows)")
        time.sleep(0.2)

    # Step 2 (optional): enrich columns used by v_politician_cards, without null overwrites
    if ENRICH_COLUMNS:
        print("Enriching view-friendly columns (politician_id, profile_image_url, short_bio, headline, detailed_bio, political_party)...")

        enriched = 0
        for p in profiles:
            profile_id = str(p.get("id") or "").strip()
            name = (p.get("name") or "").strip()
            category = (p.get("category") or "").strip()

            patch: Dict[str, Any] = {}

            politician_id = pol_map.get(name)
            if politician_id is not None:
                patch["politician_id"] = politician_id

            image_url = p.get("imageUrl") or p.get("image_url")
            if image_url:
                patch["profile_image_url"] = image_url

            short_bio = p.get("shortBio") or p.get("short_bio")
            if short_bio:
                patch["short_bio"] = short_bio

            detailed_bio = p.get("detailedBio") or p.get("detailed_bio")
            if detailed_bio:
                patch["detailed_bio"] = detailed_bio

            if category:
                patch["headline"] = category

            party = party_from_category(category)
            if party:
                patch["political_party"] = party

            if not patch:
                continue

            status, body = patch_profile(profile_id, patch)
            if status >= 300:
                print(f"[PATCH] ERROR id={profile_id} {status}: {body}")
                raise SystemExit(1)

            enriched += 1

        print(f"Enrichment done. Patched {enriched} profiles.")

    print("Done.")


if __name__ == "__main__":
    main()
