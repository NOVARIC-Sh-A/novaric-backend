import os
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Import your utility and scoring modules
from utils.scoring import generate_paragon_scores_from_metrics
# NOTE: Assume a new function is needed to transform raw data.
# from utils.metrics_ingest import ingest_raw_signals 
from mock_profiles import PROFILES as MOCK_PROFILES 


# --- Supabase Client Initialization ---
load_dotenv()
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
# Use the SERVICE_ROLE_KEY for the backend (necessary for database write access)
SUPABASE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") 

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not found in environment.")
    
SUPABASE: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def transform_mock_to_db_format(profiles: List[Dict]) -> List[Dict]:
    """
    Transforms the local mock data (for testing) into the format expected 
    by the Supabase 'paragon_scores' table.
    
    NOTE: In a live system, this function would transform the output of 
    generate_paragon_scores (which is calculated from raw data) into 
    the final DB schema. For now, we extract from the mock data's structure.
    """
    db_records = []
    for profile in profiles:
        # Get the analysis (Paragon or Maragon)
        analysis_list = profile.get("paragonAnalysis") or profile.get("maragonAnalysis")
        if not analysis_list:
            continue
            
        # The frontend needs an overall score, so let's calculate/extract it again
        total_score = sum(item["score"] for item in analysis_list)
        overall_score = round(total_score / len(analysis_list))
        
        # Prepare the dimensions as a JSON object (Postgres JSONB column)
        dimension_data = {
            item["dimension"]: {
                "score": item["score"],
                "peerAverage": item["peerAverage"],
                "commentary": item["commentary"],
            } for item in analysis_list
        }
        
        db_records.append({
            "profile_id": profile["id"], # Assuming this matches the 'politicians' table FK
            "overall_score": overall_score,
            "profile_name": profile["name"], # Denormalize for easier reading/querying
            "dimension_scores": dimension_data,
            "last_updated": "now()", # Supabase should handle this automatically
        })
        
    return db_records


def run_etl_pipeline():
    """
    1. EXTRACT: Scrape and fetch raw data (MOCK STAGE)
    2. TRANSFORM: Calculate scores (MOCK STAGE)
    3. LOAD: Write scores to Supabase (LIVE STAGE)
    """
    print("--- Starting NOVARIC ETL Pipeline ---")
    
    # === 1 & 2. MOCK EXTRACT & TRANSFORM STAGE (Using static PROFILES for now) ===
    # Replace the following line when integrating real scrapers:
    # final_scored_profiles = generate_paragon_scores_from_metrics(...)
    final_scored_profiles = MOCK_PROFILES
    
    # Transform to the required Supabase format (matching the target table schema)
    db_records = transform_mock_to_db_format(final_scored_profiles)

    if not db_records:
        print("Pipeline finished: No records to update.")
        return

    # === 3. LIVE LOAD STAGE: Write to Supabase ===
    try:
        # Use the upsert method: insert if profile_id doesn't exist, update if it does
        # NOTE: 'profile_id' must be the primary key or a unique column in 'paragon_scores'
        response = SUPABASE.table('paragon_scores').upsert(
            db_records, 
            on_conflict='profile_id' # CRITICAL: Replace with your actual unique constraint/PK
        ).execute()
        
        if response.error:
            raise Exception(f"Supabase write error: {response.error.message}")

        print(f"Pipeline Succeeded: Successfully UPSERTED {len(db_records)} records to 'paragon_scores'.")
        
    except Exception as e:
        print(f"Pipeline FAILED at LOAD stage: {e}")
        # Optional: send alert/notification

    print("--- ETL Pipeline Finished ---")


if __name__ == "__main__":
    run_etl_pipeline()