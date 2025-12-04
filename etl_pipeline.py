import os
from typing import List, Dict, Any

from supabase import create_client, Client
from dotenv import load_dotenv

# We ONLY use the mock profiles for now – they already have paragonAnalysis
from mock_profiles import PROFILES as MOCK_PROFILES

# -------------------------------------------------------------------
# Supabase client
# -------------------------------------------------------------------
load_dotenv()

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SSUPABASE_SERVICE_ROLE_KEY")  # service role

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL or SSUPABASE_SERVICE_ROLE_KEY not found in environment.")

SUPABASE: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def transform_mock_to_db_format(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Take the local MOCK_PROFILES (which already contain paragonAnalysis / maragonAnalysis)
    and convert them to the schema of the Supabase table `paragon_scores`.
    """
    db_records: List[Dict[str, Any]] = []

    for profile in profiles:
        # Prefer PARAGON analysis if present, otherwise MARAGON
        analysis_list = (
            profile.get("paragonAnalysis")
            or profile.get("maragonAnalysis")
        )

        if not analysis_list:
            continue

        # Overall score = mean of all dimension scores
        total_score = sum(item.get("score", 0) for item in analysis_list)
        count = len(analysis_list)
        overall_score = round(total_score / count) if count else 0

        # Map each dimension -> detailed scores
        dimension_data = {
            item["dimension"]: {
                "score": item.get("score", 0),
                "peerAverage": item.get("peerAverage"),
                "commentary": item.get("commentary"),
            }
            for item in analysis_list
        }

        db_records.append(
            {
                "profile_id": profile["id"],        # must match FK/unique key in DB
                "profile_name": profile["name"],    # denormalised for readability
                "overall_score": overall_score,
                "dimension_scores": dimension_data, # JSONB column in Postgres
                "last_updated": "now()",            # evaluated by Postgres
            }
        )

    return db_records


def run_etl_pipeline() -> None:
    """
    MOCK ETL:
      1) Use MOCK_PROFILES (already fully scored).
      2) Transform them to DB schema.
      3) Upsert into Supabase `paragon_scores`.
    """
    print("🚀 NOVARIC PARAGON – ETL Pipeline (MOCK MODE)")
    print("===================================================")

    # 1) Extract + Transform (mock data)
    final_scored_profiles = MOCK_PROFILES
    print(f"✔ Loaded {len(final_scored_profiles)} mock profiles with PARAGON analysis")

    db_records = transform_mock_to_db_format(final_scored_profiles)
    if not db_records:
        print("⚠ No records prepared for Supabase – check mock_profiles structure.")
        return

    print(f"✔ Prepared {len(db_records)} records for Supabase")

    # 2) Load into Supabase
    try:
        response = (
            SUPABASE
            .table("paragon_scores")
            .upsert(db_records, on_conflict="profile_id")  # profile_id must be unique
            .execute()
        )

        if getattr(response, "error", None):
            raise Exception(response.error)

        print(f"🎯 ETL SUCCESS – upserted {len(db_records)} records into `paragon_scores`")

    except Exception as e:
        print("❌ ETL FAILED during Supabase upsert")
        print(e)

    print("===================================================")
    print("🏁 ETL finished.")


if __name__ == "__main__":
    run_etl_pipeline()
