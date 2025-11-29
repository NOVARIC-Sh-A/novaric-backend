# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from mock_profiles import PROFILES
from utils.scoring import generate_paragon_scores

app = FastAPI(
    title="NOVARIC Backend",
    description="Dynamic scoring API for NOVARIC® AI-Powered News",
    version="1.1.0",
)

# -------------------------------------------------------------
# CORS
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Models
# -------------------------------------------------------------
class AnalysisRequest(BaseModel):
    ids: List[str]
    category: str


class AnalysisResponseItem(BaseModel):
    id: str
    overallScore: int
    dimensions: Dict[str, int]


class AnalysisBatchResponse(BaseModel):
    analyses: List[AnalysisResponseItem]


# -------------------------------------------------------------
# Root Health Check
# -------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "NOVARIC Backend is running"}


# -------------------------------------------------------------
# Profiles Endpoints
# -------------------------------------------------------------
@app.get("/api/profiles")
def get_profiles():
    return PROFILES


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    for p in PROFILES:
        if p["id"] == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")


# -------------------------------------------------------------
# DYNAMIC ANALYSIS BATCH ENDPOINT
# -------------------------------------------------------------
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    results = []

    for profile_id in request.ids:
        profile = next((p for p in PROFILES if p["id"] == profile_id), None)

        if not profile:
            continue

        # 🔥 dynamic scoring HERE:
        analysis = generate_paragon_scores(
            name=profile["name"],
            category=request.category,
            zodiac=profile.get("zodiacSign", "Unknown")
        )

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=analysis["overall"],
                dimensions=analysis["dimensions"]
            )
        )

    return AnalysisBatchResponse(analyses=results)
