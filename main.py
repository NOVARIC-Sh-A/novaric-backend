from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NOVARIC Backend",
    description="API for NOVARIC® AI-Powered News profiles",
    version="1.0.0",
)

# --- CORS: allow calls from your frontend (Cloud Run) ---
# For now we keep it open (*) so it works in all environments.
# Later, we can restrict to your exact frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # TODO: later put your Cloud Run URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory mock data (we can replace with real data later)
mock_profiles = [
    {
        "id": "edi_rama",
        "personalInfo": {
            "fullName": "Edi Rama",
            "party": "Partia Socialiste",
            "title": "Kryeministër",
            "imageUrl": "",
        },
        "paragonScores": {},
        "performanceAnalysis": {},
        "kapschAnalysis": {},
    },
    {
        "id": "sali_berisha",
        "personalInfo": {
            "fullName": "Sali Berisha",
            "party": "Partia Demokratike",
            "title": "Ish-kryeministër",
            "imageUrl": "",
        },
        "paragonScores": {},
        "performanceAnalysis": {},
        "kapschAnalysis": {},
    },
]


@app.get("/")
def root():
    """Simple health-check endpoint."""
    return {"message": "NOVARIC Backend is running"}


@app.get("/api/profiles")
def get_all_profiles():
    """Return all profiles."""
    return mock_profiles


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    """Return a single profile by ID."""
    for profile in mock_profiles:
        if profile["id"] == profile_id:
            return profile
    raise HTTPException(status_code=404, detail="Profile not found")
