import os
import json
import requests
from typing import List

from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import google.generativeai as genai

load_dotenv()

# ============================================================
# 1. DATA MODELS
# ============================================================

class MediaGenome(BaseModel):
    date_of_birth: str = Field(..., description="Birth date in ISO or textual format")
    place_of_birth: str = Field(..., description="Birthplace: city, region, country")
    career_start_year: int = Field(..., description="Approximate year career began")

    evolutionary_status: str = Field(..., description="Subject’s professional evolution")
    top_rhetoric_shift: str = Field(..., description="Most notable rhetorical shift")
    lethe_event: str = Field(..., description="Pivotal reinvention / forgetting moment")

    career_start_stats: List[int] = Field(
        ..., min_items=5, max_items=5, description="MARAGON stats at early career"
    )
    current_stats: List[int] = Field(
        ..., min_items=5, max_items=5, description="MARAGON stats at current stage"
    )


class ProfileData(BaseModel):
    name: str
    archetype: str = Field(..., description="Persona archetype")
    bio_summary: str = Field(..., description="150–250 word neutral biography")
    genome: MediaGenome


# ============================================================
# 2. SERPAPI SEARCH + SCRAPE
# ============================================================

def search_and_scrape_media(name: str) -> str:
    """
    Dragnet for media personality information.
    Extracts first 10 paragraphs from top SerpAPI results.
    """
    query = f"{name} biografia gazetari media polemika karriera intervista"
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

            page = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )

            soup = BeautifulSoup(page.content, "html.parser")
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs[:10])

            raw_text += f"\nSOURCE ({url}):\n{text}\n"

        except Exception:
            continue

    return raw_text


# ============================================================
# 3. GEMINI 2.5 FLASH — PROFILE GENERATION
# ============================================================

def analyze_profile(name: str) -> ProfileData:
    """
    Produces a NOVARIC-style structured profile using Gemini 2.5 Flash.
    """

    raw_data = search_and_scrape_media(name)

    # NEW SDK syntax
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Example schema for strict adherence
    schema_example = {
        "name": name,
        "archetype": "Investigative Maverick",
        "bio_summary": "150–250 word neutral biography.",
        "genome": {
            "date_of_birth": "YYYY-MM-DD",
            "place_of_birth": "City, Region, Country",
            "career_start_year": 2000,
            "evolutionary_status": "Summary of evolution",
            "top_rhetoric_shift": "Major rhetorical shift",
            "lethe_event": "Key reinvention moment",
            "career_start_stats": [20, 30, 25, 35, 40],
            "current_stats": [70, 80, 65, 75, 85]
        }
    }

    prompt = f"""
You are NOVARIC's clinical media analyst.

Generate a structured and neutral MARAGON profile for the media personality: "{name}".

RAW MATERIAL:
{raw_data}

Instructions:
- Maintain strict neutrality and factual tone.
- If uncertain, return "Unknown".
- MARAGON stats must contain exactly 5 integers (0–100).
- Avoid exaggeration, assumptions, or defamatory claims.
- Aim for analytical precision.

Return ONLY valid JSON following this structure:
{json.dumps(schema_example, indent=2)}
"""

    print("🧠 Running Gemini 2.5 Flash media profile analysis...")

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.25}
    )

    json_text = response.text.strip()

    # Remove markdown fencing if present
    if json_text.startswith("```"):
        json_text = json_text.strip("`").replace("json", "", 1).strip()

    return ProfileData.model_validate_json(json_text)


# ============================================================
# 4. TEST RUN
# ============================================================

if __name__ == "__main__":
    target = "Blendi Fevziu"
    profile = analyze_profile(target)

    print("\n----- MEDIA DOSSIER -----")
    print(profile.model_dump_json(indent=2, ensure_ascii=False))
