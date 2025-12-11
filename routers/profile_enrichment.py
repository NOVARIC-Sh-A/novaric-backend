# routers/profile_enrichment.py

from fastapi import APIRouter, HTTPException, Depends
from supabase import create_client, Client
from typing import Any, Dict

from profile_advisor import ProfileAdvisor
from schemas import VipProfileResponse   # <-- FIXED: Now importing correctly

router = APIRouter(
    prefix="/api",
    tags=["Profile Enrichment"]
)

# ---------------------------------------------------------------------
# Supabase client initialization (replace with env vars in production)
# ---------------------------------------------------------------------
SUPABASE_URL = "https://YOUR_URL.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------------------------------
# GET /api/profile/{profile_id}
# Returns the enriched VIP Profile
# ---------------------------------------------------------------------
@router.get("/profile/{profile_id}", response_model=VipProfileResponse)
async def get_profile(profile_id: str, supabase: Client = Depends(get_supabase)) -> Dict[str, Any]:
    """
    Fetch the raw profile from Supabase, enrich it using the Profile Advisor,
    and return a fully structured VipProfileResponse model.
    """

    # 1. Fetch from Supabase
    result = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", profile_id)
        .single()
        .execute()
    )

    profile_data = result.data

    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")

    # 2. Run AI enrichment (ProfileAdvisor)
    advisor = ProfileAdvisor(profile_data)
    improvement_checklist = advisor.generate_checklist()

    # 3. Build response payload (matches VipProfileResponse)
    response_data = {
        **profile_data,
        "improvement_checklist": improvement_checklist
    }

    return response_data
