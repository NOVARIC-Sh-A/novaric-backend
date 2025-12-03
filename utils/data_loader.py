# utils/data_loader.py
from typing import List, Dict, Any
from utils.supabase_client import SUPABASE # Import our initialized client
from mock_profiles import PROFILES as MOCK_PROFILES # For emergency fallback

# Map the Supabase columns to the frontend's expected Dimension names
# This is a crucial step based on your screenshot and the PARAGON_DIMENSIONS list.
SCORE_DIMENSION_MAP = {
    # Supabase Column Name: Frontend Dimension Name
    "leaders...": "Assertiveness & Influence", # Assuming 'leaders...' maps to Assertiveness
    "integrity": "Accountability & Transparency",
    "public_impact": "Narrative & Communication",
    # NOTE: You need to add mappings for ALL 7 PARAGON_DIMENSIONS here 
    # if they exist as separate columns in your database.
    # The current schema suggests you are only storing 3-4 scores.
}

def transform_live_data_to_profiles(live_scores: List[Dict], politicians: List[Dict]) -> List[Dict]:
    """
    Transforms the flat Supabase JOIN result into the VipProfile structure.
    """
    
    # Create a quick lookup map for scores
    score_map = {str(s['politician_id']): s for s in live_scores}
    
    final_profiles = []
    
    for politician_profile in politicians: # Politicians comes from the DB in a real scenario
        politician_id = str(politician_profile['id'])
        score_record = score_map.get(politician_id)
        
        if not score_record:
            # Skip politicians without a score or fill with defaults
            continue

        # 1. Map the flat scores to the rich 'paragonAnalysis' list structure
        paragon_analysis = []
        for db_col, fe_dim in SCORE_DIMENSION_MAP.items():
            score_value = score_record.get(db_col)
            if score_value is not None:
                 # NOTE: You will need to fetch/store 'peerAverage' and 'globalBenchmark' 
                 # separately or hardcode them if they aren't in the DB.
                paragon_analysis.append({
                    "dimension": fe_dim,
                    "score": int(score_value),
                    "peerAverage": 65,    # MOCK FALLBACK for missing data
                    "globalBenchmark": 70, # MOCK FALLBACK for missing data
                    "commentary": "Ky vlerësim është marrë nga baza e të dhënave të cilat janë gjeneruar nga modelet e analizës. (LIVE DATA)",
                })
        
        # 2. Build the final VipProfile object
        new_profile = {
            # Use data from a politicians table if you have one, 
            # for now, use the mock data structure and inject scores.
            "id": politician_profile["id"], 
            "name": politician_profile["name"],
            "imageUrl": politician_profile["imageUrl"], # Assuming this is available
            "category": politician_profile["category"],
            "shortBio": politician_profile["shortBio"],
            "zodiacSign": politician_profile["zodiacSign"],
            "overall_score_live": score_record['overall_score'], # Store overall for quick retrieval
            "paragonAnalysis": paragon_analysis,
        }
        
        final_profiles.append(new_profile)
        
    return final_profiles

def load_profiles_data() -> List[Dict]:
    """
    The central function to load profiles, switching between LIVE and MOCK data.
    """
    # Check environment variable to decide data source
    if os.environ.get("USE_MOCK_DATA") == "True":
        print("Loading profiles from MOCK_PROFILES.")
        return MOCK_PROFILES
        
    try:
        # NOTE: This requires fetching the 'politicians' table AND the 'paragon_scores' table.
        # This is a SIMPLIFIED implementation.
        
        # 1. Fetch live scores
        scores_response = SUPABASE.table('paragon_scores').select('*').execute()
        live_scores = scores_response.data if scores_response.data else []
        
        # 2. Fetch politician profiles (Assuming 'politicians' table exists)
        # For simplicity, we use MOCK_PROFILES as the source for politician metadata, 
        # but in production, this should also come from a 'politicians' table in Supabase.
        politicians_metadata = MOCK_PROFILES 

        if not live_scores:
            print("Supabase returned no live scores. Falling back to MOCK_PROFILES.")
            return MOCK_PROFILES

        # 3. Transform and Merge
        print(f"Loading {len(live_scores)} live scores from Supabase.")
        return transform_live_data_to_profiles(live_scores, politicians_metadata)
        
    except Exception as e:
        print(f"FATAL ERROR loading from Supabase: {e}. Falling back to MOCK_PROFILES.")
        return MOCK_PROFILES