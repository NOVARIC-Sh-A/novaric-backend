from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Import your existing pipeline functions
from bio_enricher import analyze_profile as analyze_media_profile
from bio_hunter import analyze_politician

router = APIRouter(
    prefix="/api/profiles",
    tags=["Profile Enrichment"]
)

# ==============================
# REQUEST MODELS
# ==============================

class MediaProfileRequest(BaseModel):
    name: str


class PoliticianProfileRequest(BaseModel):
    name: str
    country: Optional[str] = "Albania"


# ==============================
# MEDIA PERSONALITY ENDPOINT
# ==============================

@router.post("/media")
def generate_media_profile(payload: MediaProfileRequest):
    """
    Generates MARAGON-style enriched media personality profiles.
    """
    try:
        profile = analyze_media_profile(payload.name)
        return profile.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# POLITICIAN ENDPOINT
# ==============================

@router.post("/politician")
def generate_politician_profile(payload: PoliticianProfileRequest):
    """
    Generates structured PARAGON-ready political profiles.
    """
    try:
        profile = analyze_politician(payload.name, payload.country)
        return profile.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
