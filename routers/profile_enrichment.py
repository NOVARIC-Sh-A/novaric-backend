from fastapi import APIRouter, HTTPException, Depends
from supabase import create_client, Client
from profile_advisor import ProfileAdvisor

router = APIRouter()

# Example Supabase client init (update with your real values or dependency-injection)
SUPABASE_URL = "https://YOUR_URL.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@router.get("/profile/{profile_id}", response_model=VipProfileResponse)
async def get_profile(profile_id: str, supabase: Client = Depends(get_supabase)):

    # 1. Fetch raw profile from Supabase
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

    # 2. Run the Profile Advisor (AI psychologist)
    advisor = ProfileAdvisor(profile_data)
    improvement_checklist = advisor.generate_checklist()

    # 3. Attach the checklist to the response
    response_data = {
        **profile_data,
        "improvement_checklist": improvement_checklist
    }

    return response_data
