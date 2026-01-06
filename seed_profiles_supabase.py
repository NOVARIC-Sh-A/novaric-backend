import os
import json
import math
import urllib.request
import urllib.error

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
JSON_PATH = os.environ.get("PROFILES_JSON", "profiles_seed.json")

TABLE = os.environ.get("SUPABASE_TABLE", "profiles")  # schema is public by default in PostgREST
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "200"))

def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def postgrest_upsert(rows):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?on_conflict=id"
    data = json.dumps(rows, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            # merge-duplicates updates existing rows; do not require all cols present
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, body

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    # Convert each profile dict into a row:
    # - id: required for on_conflict
    # - payload: full profile JSON
    rows = []
    for p in profiles:
        pid = p.get("id")
        if not pid:
            continue
        rows.append({
            "id": str(pid),
            "payload": p,
        })

    total = len(rows)
    if total == 0:
        raise SystemExit("No rows to insert (check JSON file).")

    print(f"Seeding {total} profiles into public.{TABLE} in batches of {BATCH_SIZE}...")

    batches = list(chunked(rows, BATCH_SIZE))
    for i, batch in enumerate(batches, start=1):
        try:
            status, body = postgrest_upsert(batch)
            print(f"[{i}/{len(batches)}] OK {status}: upserted {len(batch)} rows")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"[{i}/{len(batches)}] ERROR {e.code}: {err_body}")
            raise

    print("Done.")

if __name__ == "__main__":
    main()
