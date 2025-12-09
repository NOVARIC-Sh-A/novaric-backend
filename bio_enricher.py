import os
import json
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
    date_of_birth: str
    place_of_birth: str
    career_start_year: int

    evolutionary_status: str
    top_rhetoric_shift: str
    lethe_event: str

    career_start_stats: List[int]
    current_stats: List[int]


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
            text = " ".join(p.get_text() for p in paragraphs[:10])

            raw_text += f"\nSOURCE ({url}):\n{text}\n"

        except Exception:
            continue

    return raw_text


# ============================================
# 3. GEMINI 2.5 FLASH ANALYSIS
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
3. Identify Lethe Event.
4. Generate MARAGON stats for early career vs current.
5. Provide a neutral and clinical summary.

Return ONLY valid JSON in the format:

{{
  "name": "...",
  "archetype": "...",
  "bio_summary": "...",
  "genome": {{
      "date_of_birth": "...",
      "place_of_birth": "...",
      "career_start_year": 0,
      "evolutionary_status": "...",
      "top_rhetoric_shift": "...",
      "lethe_event": "...",
      "career_start_stats": [0,0,0,0,0],
      "current_stats": [0,0,0,0,0]
  }}
}}
"""

    print("🧠 Running Gemini 2.5 Flash analysis...")

    resp = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=system_prompt,
        generation_config={"temperature": 0.3}
    )

    json_text = resp.text.strip()

    # Strip Markdown markers if needed
    if json_text.startswith("```"):
        json_text = json_text.strip("```").replace("json", "").strip()

    return ProfileData.model_validate_json(json_text)


# ============================================
# 4. TEST RUN
# ============================================

if __name__ == "__main__":
    target = "Blendi Fevziu"
    profile = analyze_profile(target)

    print("\n----- DOSSIER -----")
    print(profile.json(indent=2))
