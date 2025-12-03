# utils/data_loader.py
import os
import sys
from os.path import dirname, join, abspath
from typing import List, Dict, Any

# ================================================================
# 1. IMPORTS
# Use REST-based Supabase fetchers (no SDK functions or .execute())
# ================================================================
from utils.supabase_client import fetch_live_paragon_data

try:
    # Standard import
    from mock_profiles import PROFILES as MOCK_PROFILES
except ImportError:
    # Ensure root is on PYTHONPATH during load
    sys.path.insert(0, abspath(join(dirname(__file__), '..')))
    from mock_profiles import PROFILES as MOCK_PROFILES
    sys.path.pop(0)


# ================================================================
# 2. PARAGON DIMENSION MAP
# Map Supabase columns → frontend dimension names
# ================================================================
SCORE_DIMENSION_MAP: Dict[str, str] = {
    "leadership": "Assertiveness & Influence",
    "integrity": "Accountability & Transparency",
    "public_impact": "Narrative & Communication",
    # add more as needed…
}


# ================================================================
# 3. Transform Supabase rows → VipProfile format
# ================================================================
def transform_live_data_to_profiles(
    live_scores: List[Dict], mock_profiles: List[Dict]
) -> List[Dict]:

    # Map: { politician_id: score_record }
    score_map = {str(s["politician_id"]): s for s in live_scores}

    final_profiles = []

    for mock_profile in mock_profiles:

        profile_id = str(mock_profile.get("id"))
        score_record = score_map.get(profile_id)

        new_profile = mock_profile.copy()

        if score_record:
            # Inject overall score + metadata
            new_profile["overall_score_live"] = score_record.get("overall_score")
            new_profile["dynamicScore"] = score_record.get("overall_score")
            new_profile["calculated_at"] = score_record.get("calculated_at")

            # Build PARAGON dimension list
            paragon_analysis = []
            for db_col, fe_dim in SCORE_DIMENSION_MAP.items():
                score_value = score_record.get(db_col)
                if score_value is not None:
                    paragon_analysis.append({
                        "dimension": fe_dim,
                        "score": int(score_value),
                        "peerAverage": 65,
                        "globalBenchmark": 70,
                        "commentary": (
                            f"Ky vlerësim është marrë nga baza e të dhënave të "
                            f"gjeneruara nga modelet e analizës. "
                            f"(LIVE SCORE: {score_record.get('calculated_at')})"
                        ),
                    })

            new_profile["paragonAnalysis"] = paragon_analysis

        final_profiles.append(new_profile)

    return final_profiles


# ================================================================
# 4. Main loader: MOCK or LIVE
# ================================================================
def load_profiles_data() -> List[Dict]:
    """
    Central function used by FastAPI to load data.

    - If USE_LIVE_DB=True → fetch from Supabase REST.
    - Otherwise → fallback to mock data.
    """
    use_live = os.environ.get("USE_LIVE_DB") == "True"

    if not use_live:
        print("Backend: Loading MOCK_PROFILES (USE_LIVE_DB != True).")
        return MOCK_PROFILES

    try:
        print("Backend: Fetching live PARAGON scores from Supabase REST…")
        live_scores = fetch_live_paragon_data()

        if not live_scores:
            print("Supabase REST returned 0 rows → fallback to MOCK.")
            return MOCK_PROFILES

        print(f"Backend: Merging {len(live_scores)} live scores.")
        return transform_live_data_to_profiles(live_scores, MOCK_PROFILES)

    except Exception as e:
        print(f"ERROR fetching live DB: {e} → Using MOCK_PROFILES.")
        return MOCK_PROFILES
