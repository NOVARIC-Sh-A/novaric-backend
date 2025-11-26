from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils.load_profiles import load_profiles

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later replace with Cloud Run public URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES ---
@app.get("/")
def root():
    return {"message": "NOVARIC Backend is running"}

@app.get("/api/profiles")
def get_all_profiles():
    return load_profiles()

@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    profiles = load_profiles()
    profile = next((p for p in profiles if p["id"] == profile_id), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
