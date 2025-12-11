# backend/profile_update.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.supabase_client import supabase_upsert
import datetime

router = APIRouter(prefix="/api", tags=["Profiles"])

# ---------------------------
# Request Body Schema
# ---------------------------
class UpdateProfileImageRequest(BaseModel):
    profileId: str
    newImageUrl: str


# ---------------------------
# Endpoint Implementation
# ---------------------------
@router.post("/update-profile-image")
def update_profile_image(payload: UpdateProfileImageRequest):
    profile_id = payload.profileId
    new_url = payload.newImageUrl

    if not profile_id or not new_url:
        raise HTTPException(status_code=400, detail="Missing profileId or newImageUrl")

    # Prepare the row for UPSERT
    row = {
        "id": profile_id,
        "profile_image_url": new_url,
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

    try:
        # Supabase UPSERT (MERGE on conflict: id)
        supabase_upsert(
            table="profiles",
            records=[row],
            conflict_col="id"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase update failed: {e}")

    return {
        "status": "success",
        "message": "Profile image updated.",
        "id": profile_id,
        "profile_image_url": new_url
    }
