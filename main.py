from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import random
import hashlib

app = FastAPI(
    title="NOVARIC Backend",
    description="API for NOVARIC® AI-Powered News profiles & analysis",
    version="1.0.0",
)

# --- CORS: allow calls from your frontend (Cloud Run) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # later you can restrict to your Cloud Run URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# BASIC MOCK PROFILES (kept simple – your real profiles live in frontend)
# -------------------------------------------------------------------
mock_profiles = [
    {
        "id": "vip1",
        "personalInfo": {
            "fullName": "Edi Rama",
            "party": "Partia Socialiste",
            "title": "Kryeministër",
            "imageUrl": "",
        },
    },
    {
        "id": "vip2",
        "personalInfo": {
            "fullName": "Sali Berisha",
            "party": "Partia Demokratike",
            "title": "Ish-kryeministër",
            "imageUrl": "",
        },
    },
]


@app.get("/")
def root():
    """Simple health-check endpoint."""
    return {"message": "NOVARIC Backend is running"}


@app.get("/api/profiles")
def get_all_profiles():
    """Return basic mock profiles (for testing)."""
    return mock_profiles


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    """Return a single mock profile by ID (for testing)."""
    for profile in mock_profiles:
        if profile["id"] == profile_id:
            return profile
    raise HTTPException(status_code=404, detail="Profile not found")


# -------------------------------------------------------------------
# PARAGON / MARAGON – FULL DETAILED ANALYSIS (OPTION 1)
# -------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    ids: List[str]
    category: str = "political"  # "political", "media", "business", etc.


# We model the AI fields as a nested structure
class DimensionAI(BaseModel):
    trend: float          # e.g. +2.3 points vs last period
    confidence: float     # 0–1
    volatility: float     # 0–1, how unstable the score is
    summary: str
    sources: List[str]


class DimensionAnalysis(BaseModel):
    name: str
    score: int
    peerAverage: int
    globalBenchmark: int
    ai: DimensionAI


class ProfileAnalysis(BaseModel):
    id: str
    category: str
    overallScore: int
    dimensions: Dict[str, DimensionAnalysis]
    aiSummary: str


# --- Helper: deterministic random from id + dimension ----------------
def deterministic_random_int(key: str, min_val: int, max_val: int) -> int:
    """
    Generate a deterministic integer in [min_val, max_val] from a key string.
    This ensures scores are stable for the same profile & dimension.
    """
    h = hashlib.md5(key.encode("utf-8")).hexdigest()
    seed_int = int(h[:8], 16)
    rng = random.Random(seed_int)
    return rng.randint(min_val, max_val)


def deterministic_random_float(key: str, min_val: float, max_val: float) -> float:
    """
    Deterministic float in [min_val, max_val].
    """
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    seed_int = int(h[:8], 16)
    rng = random.Random(seed_int)
    return min_val + (max_val - min_val) * rng.random()


# --- Define dimension sets per category ------------------------------

POLITICAL_DIMENSIONS = [
    "Policy Engagement & Expertise",
    "Accountability & Transparency",
    "Representation & Responsiveness",
    "Assertiveness & Influence",
    "Governance & Institutional Strength",
    "Organizational & Party Cohesion",
    "Narrative & Communication",
]

MEDIA_DIMENSIONS = [
    "Ethical Compliance",
    "Crisis Professionalism",
    "Factual Accuracy & Verification",
    "Impartiality & Balance",
    "Depth of Questions & Analysis",
    "Clarity & Coherence",
    "Promotion of Critical Thinking",
]

BUSINESS_DIMENSIONS = [
    "Strategic Vision & Innovation",
    "Governance & Compliance",
    "Financial Performance",
    "Stakeholder & Community Impact",
    "Organizational Resilience",
    "Reputation & Public Influence",
]


def get_dimensions_for_category(category: str) -> List[str]:
    if category == "media":
        return MEDIA_DIMENSIONS
    if category == "business":
        return BUSINESS_DIMENSIONS
    # default
    return POLITICAL_DIMENSIONS


# --- Core generator: one profile full analysis -----------------------
def generate_profile_analysis(profile_id: str, category: str) -> Dict[str, Any]:
    dimensions_names = get_dimensions_for_category(category)

    # overallScore is an average-ish of the dimensions, but we generate it first
    overall_seed_key = f"{profile_id}:{category}:overall"
    overall_score = deterministic_random_int(overall_seed_key, 50, 95)

    dimensions: Dict[str, Dict[str, Any]] = {}

    for dim_name in dimensions_names:
        dim_key = f"{profile_id}:{category}:{dim_name}"

        score = deterministic_random_int(dim_key + ":score", 40, 95)
        peer_avg = deterministic_random_int(dim_key + ":peer", 50, 80)
        benchmark = deterministic_random_int(dim_key + ":bench", 60, 90)

        trend = round(deterministic_random_float(dim_key + ":trend", -5.0, 5.0), 2)
        confidence = round(deterministic_random_float(dim_key + ":conf", 0.7, 0.99), 2)
        volatility = round(deterministic_random_float(dim_key + ":vol", 0.05, 0.35), 2)

        ai_summary = (
            f"Dimension '{dim_name}' for profile '{profile_id}' in category '{category}' "
            f"tregon një performancë { 'mbi mesataren' if score >= peer_avg else 'nën mesataren' } "
            f"krahasuar me kolegët dhe një trend "
            f"{ 'pozitiv' if trend > 0 else 'negativ' if trend < 0 else 'neutral' }."
        )

        sources = [
            f"https://media.novaric.al/profile/{profile_id}/{dim_name.replace(' ', '%20')}",
            "https://novaric.co",
        ]

        dimensions[dim_name] = DimensionAnalysis(
            name=dim_name,
            score=score,
            peerAverage=peer_avg,
            globalBenchmark=benchmark,
            ai=DimensionAI(
                trend=trend,
                confidence=confidence,
                volatility=volatility,
                summary=ai_summary,
                sources=sources,
            ),
        ).model_dump()

    global_summary = (
        f"Profili '{profile_id}' ({category}) ka një skorë të përgjithshme rreth {overall_score}/100 "
        f"me shpërndarje të ndryshme në dimensionet PARAGON/MARAGON. "
        f"Këto të dhëna janë aktualisht të gjeneruara automatikisht si 'mock', "
        f"por struktura e API-së është gati për t'u ushqyer me analiza reale "
        f"nga motori juaj i kërkimit dhe scraping-ut."
    )

    return ProfileAnalysis(
        id=profile_id,
        category=category,
        overallScore=overall_score,
        dimensions=dimensions,
        aiSummary=global_summary,
    ).model_dump()


# --- API Endpoint: /api/profiles/analysis-batch ----------------------
@app.post("/api/profiles/analysis-batch")
def get_analysis_batch(request: AnalysisRequest) -> Dict[str, Any]:
    """
    Request body:
    {
      "ids": ["vip1", "vip2", ...],
      "category": "political" | "media" | "business"
    }

    Response:
    {
      "analyses": [
        {
          "id": "vip1",
          "category": "political",
          "overallScore": 82,
          "dimensions": {
            "Policy Engagement & Expertise": {
               "name": "...",
               "score": 78,
               "peerAverage": 71,
               "globalBenchmark": 75,
               "ai": {
                  "trend": 2.3,
                  "confidence": 0.91,
                  "volatility": 0.14,
                  "summary": "...",
                  "sources": ["...", "..."]
               }
            },
            ...
          },
          "aiSummary": "..."
        },
        ...
      ]
    }
    """
    analyses: List[Dict[str, Any]] = []

    for pid in request.ids:
        analyses.append(generate_profile_analysis(pid, request.category))

    return {"analyses": analyses}
