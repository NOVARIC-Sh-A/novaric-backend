# utils/bio_etl.py

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from .bio_scraper import scrape_profile_data

# OPTIONAL: Supabase support for loading into DB
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

_supabase_client = None

def get_supabase_client():
    """
    Lazily create a Supabase client if credentials are present.
    If not configured, returns None – so the ETL can still run
    and just output JSON/local files.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        print("ℹ️ Supabase not configured – skipping DB load step.")
        _supabase_client = None
        return None

    try:
        from supabase import create_client, Client  # type: ignore
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
        print("✅ Supabase client initialised.")
        return _supabase_client
    except Exception as e:
        print(f"⚠️ Could not initialise Supabase client: {e}")
        _supabase_client = None
        return None


# ------------------------------------------------------
# 1. EXTRACT – Load target profiles
# ------------------------------------------------------
def load_targets_from_json(path: str) -> List[Dict[str, Any]]:
    """
    Load politician profiles from a JSON file.
    JSON format (example):

    [
      { "id": 1, "name": "Edi Rama" },
      { "id": 2, "name": "Sali Berisha" }
    ]
    """
    if not os.path.exists(path):
        print(f"⚠️ Target JSON file not found at {path}.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} profiles from {path}")
        return data
    except Exception as e:
        print(f"⚠️ Failed to load JSON targets from {path}: {e}")
        return []


def get_default_targets() -> List[Dict[str, Any]]:
    """
    Fallback list – used if JSON file or DB source is not available.
    """
    names = [
        "Edi Rama", "Sali Berisha", "Ilir Meta", "Lulzim Basha",
        "Monika Kryemadhi", "Erion Veliaj", "Belind Këlliçi",
        "Bajram Begaj", "Benet Beci", "Nard Ndoka",
        "Blendi Fevziu", "Grida Duma", "Ardit Gjebrea",
        "Sokol Balla", "Eni Vasili", "Alketa Vejsiu"
    ]
    return [{"id": None, "name": n} for n in names]


def extract_targets(targets_json_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Determine where to load targets from:
    1) JSON file (if provided and found)
    2) Fallback to built-in list
    Later you can extend this to load from Supabase table 'politicians'.
    """
    if targets_json_path:
        loaded = load_targets_from_json(targets_json_path)
        if loaded:
            return loaded

    print("ℹ️ Using default built-in target list.")
    return get_default_targets()


# ------------------------------------------------------
# 2. TRANSFORM – Call scraper & shape the data
# ------------------------------------------------------
def transform_profile(raw_target: Dict[str, Any]) -> Dict[str, Any]:
    """
    For a single target (e.g. {"id": 1, "name": "Edi Rama"}),
    call scrape_profile_data() and return a normalized record.
    """
    name = raw_target.get("name")
    politician_id = raw_target.get("id")

    scraped = scrape_profile_data(name)

    # Ensure standard keys present
    record = {
        "politician_id": politician_id,
        "name": scraped.get("name", name),
        "dob": scraped.get("dob"),
        "age": scraped.get("age"),
        "zodiac": scraped.get("zodiac"),
        "found": scraped.get("found", False),
        "error": scraped.get("error"),
        "source_system": "bio_scraper_v2",
        "last_scraped_at": datetime.utcnow().isoformat() + "Z",
    }

    return record


def run_transform_step(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform all targets into cleaned, enriched bio records.
    """
    results: List[Dict[str, Any]] = []
    print(f"🔧 Transforming {len(targets)} profiles...")
    for t in targets:
        name = t.get("name")
        print(f"   ➜ Scraping {name} ...")
        try:
            record = transform_profile(t)
            if record["found"]:
                print(
                    f"      ✔ {record['name']}: {record['dob']} | "
                    f"{record['age']} yrs | {record['zodiac']}"
                )
            else:
                print(
                    f"      ⚠ {record['name']}: no DOB ({record.get('error')})"
                )
            results.append(record)
        except Exception as e:
            print(f"      ❌ Failed to process {name}: {e}")
    return results


# ------------------------------------------------------
# 3. LOAD – Save to Supabase and/or JSON snapshot
# ------------------------------------------------------
def load_into_supabase(records: List[Dict[str, Any]], table_name: str = "politician_bio") -> None:
    """
    Load records into Supabase table via upsert (by name or politician_id).
    You can adjust the conflict target depending on your schema.
    """
    client = get_supabase_client()
    if not client:
        print("ℹ️ Skipping Supabase load – client not available.")
        return

    if not records:
        print("ℹ️ No records to load into Supabase.")
        return

    # Decide conflict target: prefer politician_id if present
    conflict_column = "politician_id" if any(r.get("politician_id") is not None for r in records) else "name"

    try:
        print(f"⬆️ Upserting {len(records)} records into Supabase table '{table_name}' (on {conflict_column})...")
        # Supabase Python doesn't support upsert with conflict via simple syntax everywhere,
        # but we can use RPC or rely on PostgREST 'on_conflict' if available.
        # Here we chunk inserts for safety.

        chunk_size = 50
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            response = client.table(table_name).upsert(chunk, on_conflict=conflict_column).execute()
            if getattr(response, "error", None):
                print(f"   ⚠ Supabase error in chunk {i // chunk_size}: {response.error}")
        print("✅ Supabase load completed.")
    except Exception as e:
        print(f"❌ Failed to load into Supabase: {e}")


def write_snapshot_to_file(records: List[Dict[str, Any]], path: str = "data/bio_snapshot.json") -> None:
    """
    Writes the ETL result to a local JSON file.
    This is useful for debugging, offline analysis,
    and frontend mock data injection.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"💾 Snapshot written to {path}")
    except Exception as e:
        print(f"⚠️ Failed to write snapshot to {path}: {e}")


# ------------------------------------------------------
# 4. MAIN PIPELINE ENTRYPOINT
# ------------------------------------------------------
def run_bio_etl(targets_json_path: Optional[str] = None,
                snapshot_path: str = "data/bio_snapshot.json",
                load_to_supabase: bool = True) -> None:
    """
    Full ETL:
    1) Extract list of targets
    2) Transform via scraping
    3) Load into Supabase (optional)
    4) Write local JSON snapshot
    """
    print("🚀 Starting NOVARIC Bio ETL Pipeline")
    print("=" * 70)

    # EXTRACT
    targets = extract_targets(targets_json_path)
    if not targets:
        print("❌ No targets available – aborting.")
        return

    # TRANSFORM
    records = run_transform_step(targets)

    # LOAD – Supabase
    if load_to_supabase:
        load_into_supabase(records)

    # LOAD – Local snapshot
    write_snapshot_to_file(records, snapshot_path)

    print("=" * 70)
    print("✅ Bio ETL finished successfully.")


if __name__ == "__main__":
    # You can optionally pass a JSON path via env:
    # BIO_TARGETS_JSON=./data/politicians.json python -m utils.bio_etl
    targets_json = os.environ.get("BIO_TARGETS_JSON")
    run_bio_etl(targets_json_path=targets_json)
