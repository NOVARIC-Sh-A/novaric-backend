import json
import os
import math
import urllib.request
import urllib.error

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TABLE = os.environ.get("SUPABASE_TABLE", "profiles")
JSON_PATH = os.environ["PROFILES_JSON"]
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "200"))

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

def extract_party(category: str | None) -> str | None:
    if not category:
        return None
    if "(" in category and ")" in category:
        return category.split("(")[-1].split(")")[0]
    return None

def load_profiles():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(profile: dict) -> dict:
    return {
        "id": profile["id"],
        "name": profile.get("name"),
        "short_bio": profile.get("shortBio"),
        "detailed_bio": profile.get("detailedBio"),
        "zodiac_sign": profile.get("zodiacSign"),
        "political_party": extract_party(profile.get("category")),
        "payload": profile
    }

def upsert_batch(batch):
    url = f"{SUPABASE_URL}/rest/v1/{TABLE}?on_conflict=id"
    data = json.dumps(batch, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers=HEADERS,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    profiles = load_profiles()
    total = len(profiles)
    batches = math.ceil(total / BATCH_SIZE)

    print(f"Seeding {total} profiles into public.{TABLE} in {batches} batch(es)...")

    for i in range(batches):
        chunk = profiles[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        payload = [normalize(p) for p in chunk]

        status, body = upsert_batch(payload)

        if status not in (200, 201):
            print(f"[{i+1}/{batches}] ERROR {status}: {body}")
            raise SystemExit(1)

        print(f"[{i+1}/{batches}] OK ({len(payload)} records)")

    print("✔ Seeding complete.")

if __name__ == "__main__":
    main()
