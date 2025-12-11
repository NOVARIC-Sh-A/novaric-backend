# routers/profile_enrichment.py

import os
from functools import lru_cache
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from supabase import create_client, Client

from profile_advisor import ProfileAdvisor
from schemas import VipProfileResponse


router = APIRouter(
    prefix="/api",
    tags=["Profile Enrichment"]
)


# -----------------------------------------------------------
# Supabase configuration (should come from environment vars)
# -----------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# -----------------------------------------------------------
# Lazy-loaded Supabase Client (pytest-safe)
# -----------------------------------------------------------
@lru_cache()
def get_supabase() -> Client:
    """
    Lazy initialization. Supabase client is created ONLY when endpoint is called,
    NOT during module import (which avoids pytest freezing).
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials are not configured.")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------------------------------------
# GET /api/profile/{profile_id}
# -----------------------------------------------------------
@router.get("/profile/{profile_id}", response_model=VipProfileResponse)
async def get_profile(profile_id: str, supabase: Client = Depends(get_supabase)) -> Dict[str, Any]:
    """
    Fetch a VIP profile from Supabase, enrich it using ProfileAdvisor,
    and return a structured VipProfileResponse object.
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

    # 2. Run ProfileAdvisor (AI psychologist)
    advisor = ProfileAdvisor(profile_data)
    improvement_checklist = advisor.generate_checklist()

    # 3. Build standardized response
    return {
        **profile_data,
        "improvement_checklist": improvement_checklist,
    }
