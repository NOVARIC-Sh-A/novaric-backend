import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field
from typing import List

from google import genai


# ============================================
# 1. DATA MODELS
# ============================================

class MediaGenome(BaseModel):
    date_of_birth: str = Field(description="YYYY-MM-DD or 'Unknown'")
    place_of_birth: str = Field(description="City, Country")
    career_start_year: int = Field(description="Year they started in media")

    evolutionary_status: str = Field(
        description="One of: Ascending, Stagnant, Regressing, Compromised"
    )
    top_rhetoric_shift: str = Field(description="Short phrase describing rhetoric evolution")
    lethe_event: str = Field(description="Topic they avoid discussing recently")

    career_start_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] at career start"
    )
    current_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] today"
    )


class ProfileData(BaseModel):
    name: str
    archetype: str
    bio_summary: str
    genome: MediaGenome


# ============================================
# 2. SEARCH + SCRAPE (DRAGNET)
# ============================================

def search_and_scrape(query: str) -> str:
    print(f"🔎 Scanning the web for: {query}...")

    search = GoogleSearch({
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
        "num": 3
    })

    results = search.get_dict()
    raw_text = ""

    for result in results.get("organic_results", []):
        try:
            url = result["link"]
            print(f"   → Extracting: {url}")

            page = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")

            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text() for p in paragraphs[:10]])

            raw_text += f"\nSOURCE ({url}):\n{text}\n"

        except Exception:
            continue

    return raw_text


# ============================================
# 3. GEMINI 1.5 ANALYSIS (NEW ENGINE)
# ============================================

def analyze_profile(name: str):
    raw_data = search_and_scrape(f"{name} biografia gazetari media polemika")

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    system_prompt = f"""
You are NOVARIC's clinical media analyst.
Analyze the media personality: {name}

RAW MATERIAL:
{raw_data}

Your task:
1. Infer evolutionary_status.
2. Identify rhetoric shift.
3. Identify Lethe Event (topics avoided recently).
4. Generate MARAGON stats for early career vs. today.
5. Produce a neutral, clinical summary.
6. Return ONLY valid JSON following this schema:

{ProfileData.model_json_schema()}
"""

    print("🧠 Running Gemini 1.5 Flash analysis...")

    resp = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=system_prompt,
        generation_config={"temperature": 0.3}
    )

    json_text = resp.text.strip()

    # Parse into Pydantic model
    return ProfileData.model_validate_json(json_text)


# ============================================
# 4. TEST RUN
# ============================================

if __name__ == "__main__":
    target = "Blendi Fevziu"
    profile = analyze_profile(target)

    print("\n----- DOSSIER -----")
    print(profile.json(indent=2))
