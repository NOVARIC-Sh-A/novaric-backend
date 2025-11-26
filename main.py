from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="NOVARIC Political Profile API",
    description="Serves mock data for politician profiles",
    version="1.0.0",
)

# ✅ VERY IMPORTANT: allow your frontend (Cloud Run) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # later you can restrict this to your Cloud Run URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple mock profiles – we can expand these later
mock_profiles = [
    {
        "id": "edi_rama",
        "personalInfo": {
            "fullName": "Edi Rama",
            "party": "Partia Socialiste",
            "title": "Kryeministër",
            "imageUrl": ""
        }
    },
    {
        "id": "sali_berisha",
        "personalInfo": {
            "fullName": "Sali Berisha",
            "party": "Partia Demokratike",
            "title": "Ish-kryeministër",
            "imageUrl": ""
        }
    }
]


@app.get("/api/profiles")
async def get_profiles():
    return mock_profiles


@app.get("/api/profiles/{profile_id}")
async def get_single_profile(profile_id: str):
    for p in mock_profiles:
        if p["id"] == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")
