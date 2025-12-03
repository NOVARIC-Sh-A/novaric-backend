# utils/data_loader.py
import os
import sys
from os.path import dirname, join, abspath
from typing import List, Dict, Any

# =================================================================
# 1. IMPORTS (ROBUSTLY handle root-level mock_profiles.py import)
# =================================================================
from utils.supabase_client import SUPABASE # Assumes supabase_client.py is correct

try:
    # Try the standard import (works if the project root is on PYTHONPATH)
    from mock_profiles import PROFILES as MOCK_PROFILES 
except ImportError:
    # Fallback for environments (like some Render setups) where main.py's import 
    # from the root does not automatically make the root a package for sub-modules.
    
    # Temporarily add the project root (.. relative to utils/) to the system path
    sys.path.insert(0, abspath(join(dirname(__file__), '..'))) 
    from mock_profiles import PROFILES as MOCK_PROFILES
    
    # Clean up the path (optional, but good practice)
    sys.path.pop(0)


# =================================================================
# 2. CORE MAPPING (Based on your Supabase 'paragon_scores' schema)
# =================================================================
SCORE_DIMENSION_MAP: Dict[str, str] = {
    # Supabase Column Name: Frontend Dimension Name (from PARAGON_DIMENSIONS)
    "leaders...": "Assertiveness & Influence",
    "integrity": "Accountability & Transparency",
    "public_impact": "Narrative & Communication",
    # Add other columns here (e.g., policy_exp: "Policy Engagement & Expertise")
    # For now, only the columns visible in your screenshot are mapped.
}

def transform_live_data_to_profiles(live_scores: List[Dict], mock_profiles: List[Dict]) -> List[Dict]:
    """
    Transforms the flat Supabase score records and merges them into the rich VipProfile structure.
    
    This function uses the mock_profiles as the source of truth for all metadata (bio, image, etc.)
    and ONLY overwrites the 'paragonAnalysis' and related score fields.
    """
    
    # Create a quick lookup map for scores using 'politician_id'
    score_map = {str(s['politician_id']): s for s in live_scores}
    
    final_profiles = []
    
    for mock_profile in mock_profiles:
        profile_id = str(mock_profile.get('id'))
        score_record = score_map.get(profile_id)
        
        # Start with the existing mock profile data (copy the original data structure)
        new_profile = mock_profile.copy()
        
        if score_record:
            # === LIVE SCORE INJECTION ===
            
            # a. Inject overall score into new fields (used by frontend merge logic)
            new_profile['overall_score_live'] = score_record.get('overall_score')
            new_profile['dynamicScore'] = score_record.get('overall_score') 
            new_profile['calculated_at'] = score_record.get('calculated_at')

            # b. Build the rich 'paragonAnalysis' list using live scores
            paragon_analysis = []
            for db_col, fe_dim in SCORE_DIMENSION_MAP.items():
                score_value = score_record.get(db_col)
                if score_value is not None:
                    paragon_analysis.append({
                        "dimension": fe_dim,
                        "score": int(score_value),
                        "peerAverage": 65,    
                        "globalBenchmark": 70, 
                        "commentary": f"Ky vlerësim është marrë nga baza e të dhënave të gjeneruara nga modelet e analizës. (LIVE SCORE: {score_record.get('calculated_at')})",
                    })
            
            # Overwrite the existing mock analysis with the live, merged data
            new_profile['paragonAnalysis'] = paragon_analysis
        
        final_profiles.append(new_profile)
        
    return final_profiles


# =================================================================
# 3. CENTRAL LOADER FUNCTION
# =================================================================

def load_profiles_data() -> List[Dict]:
    """
    The central function to load profiles, switching between LIVE (Supabase) and MOCK data.
    Controlled by the 'USE_LIVE_DB' environment variable.
    """
    # 1. Check environment variable to decide data source
    if os.environ.get("USE_LIVE_DB") != "True":
        print("Backend: Loading profiles from MOCK_PROFILES (USE_LIVE_DB != True).")
        return MOCK_PROFILES
        
    # 2. Load from LIVE Supabase Database
    try:
        # Fetch all scores from the paragon_scores table
        scores_response = SUPABASE.table('paragon_scores').select('*').execute()
        live_scores = scores_response.data if scores_response.data else []
        
        if not live_scores:
            print("Supabase returned no live scores. Falling back to MOCK_PROFILES.")
            return MOCK_PROFILES

        # 3. Transform and Merge live scores with rich mock metadata
        print(f"Backend: Loading and merging {len(live_scores)} live scores from Supabase.")
        return transform_live_data_to_profiles(live_scores, MOCK_PROFILES)
        
    except Exception as e:
        print(f"FATAL ERROR loading from Supabase: {e}. Falling back to MOCK_PROFILES.")
        # If the API or connection fails, revert to the static local mocks.
        return MOCK_PROFILES