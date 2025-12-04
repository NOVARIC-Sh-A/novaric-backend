import os
import json
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# NEW ENGINE + METRICS
from utils.data_loader import load_raw_profiles
from utils.metrics_loader import load_all_metrics
from utils.paragon_engine import run_paragon_analysis

# LOAD ENV
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

SUPABASE: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "data/export"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = f"{OUTPUT_DIR}/profiles.json"


# ------------------------------------------------------------
# TRANSFORM STEP FOR SUPABASE RECORDS
# ------------------------------------------------------------

def transform_profile_for_db(profile: Dict[str, Any]) -> Dict:
    """
    Converts PARAGON engine output to the DB schema for 'paragon_scores'.
    """

    analysis = profile.get("paragonAnalysis") or []
    if not analysis:
        return None

    total_score = sum(item["score"] for item in analysis)
    overall_score = round(total_score / len(analysis))

    dimension_scores = {
        item["dimension"]: {
            "score": item["score"],
            "peerAverage": item["peerAverage"],
            "commentary": item["commentary"],
        }
        for item in analysis
    }

    return {
        "profile_id": profile["id"],
        "profile_name": profile["name"],
        "overall_score": overall_score,
        "dimension_scores": dimension_scores,
        "last_updated": "now()"  # Postgres will evaluate this to NOW()
    }


# ------------------------------------------------------------
# FULL ETL PIPELINE
# ------------------------------------------------------------

def run_etl_pipeline():
    print("🚀 NOVARIC ETL PIPELINE STARTED")
    print("=================================================")

    # 1) LOAD RAW PROFILES (name, party, images, socials)
    profiles = load_raw_profiles()
    print(f"✔ Loaded {len(profiles)} raw profiles")

    # 2) LOAD ALL METRICS (bio, media, social)
    metrics = load_all_metrics()
    print(f"✔ Loaded metrics: {list(metrics.keys())}")

    # 3) RUN PARAGON ENGINE
    enriched_profiles = []
    for p in profiles:
        enriched = run_paragon_analysis(p, metrics)
        enriched_profiles.append(enriched)

    print(f"✔ PARAGON analysis completed for {len(enriched_profiles)} profiles")

    # 4) EXPORT TO LOCAL (for frontend & debugging)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_profiles, f, indent=2, ensure_ascii=False)

    print(f"✔ Local dataset written to {OUTPUT_FILE}")

    # 5) TRANSFORM FOR SUPABASE
    db_records = []
    for p in enriched_profiles:
        transformed = transform_profile_for_db(p)
        if transformed:
            db_records.append(transformed)

    print(f"✔ Prepared {len(db_records)} database records")

    # 6) LOAD INTO SUPABASE
    print("⬆ Uploading to Supabase 'paragon_scores'…")

    try:
        response = SUPABASE.table("paragon_scores").upsert(
            db_records,
            on_conflict="profile_id"
        ).execute()

        print(f"🎯 ETL SUCCESS — {len(db_records)} profiles written to Supabase")

    except Exception as e:
        print("❌ ETL FAILED — Error uploading to Supabase")
        print(e)

    print("=================================================")
    print("🚀 ETL PIPELINE FINISHED")


if __name__ == "__main__":
    run_etl_pipeline()
