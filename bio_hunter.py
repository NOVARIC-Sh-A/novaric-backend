import os
import json
import requests
from typing import List, Optional

from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import google.generativeai as genai

load_dotenv()

# ============================================================
# 1. DATA MODELS
# ============================================================

class PoliticianGenome(BaseModel):
    """
    Core structured signal for a politician, suitable for
    integration into PARAGON or other analytics models.
    Order of PARAGON seed dimensions:
    [Integrity, Governance, Diplomacy, Economy, Public Trust]
    """

    date_of_birth: str = Field(..., description="ISO or textual date")
    place_of_birth: str = Field(..., description="City, region, country")
    country: str = Field(..., description="Country of political activity")

    party_affiliation: str = Field(..., description="Primary party affiliation")
    ideology: str = Field(..., description="Short ideological label")
    first_elected_year: int = Field(..., description="Approx first year in office")
    current_role: str = Field(..., description="Current governmental/political role")

    key_policy_areas: List[str] = Field(..., description="Major policy domains")

    corruption_and_ethics_summary: str = Field(
        ...,
        description="Neutral summary of allegations, investigations, or clean record"
    )
    international_relations_summary: str = Field(
        ...,
        description="Neutral summary of alignment with EU/US/NATO, regional actors"
    )
    domestic_reputation_summary: str = Field(
        ...,
        description="Neutral view of domestic perception by supporters & critics"
    )

    paragon_seed_scores: List[int] = Field(
        ...,
        min_items=5,
        max_items=5,
        description="Five integers 0–100 seeding Integrity–Trust axes"
    )


class PoliticianProfile(BaseModel):
    """
    High-level structured profile wrapping the politician’s genome.
    """
    name: str
    archetype: str = Field(..., description="E.g., 'Reformer Technocrat'")
    bio_summary: str = Field(..., description="150–250 word neutral biography")
    genome: PoliticianGenome


# ============================================================
# 2. SEARCH + SCRAPE (DRAGNET)
# ============================================================

def search_and_scrape_politician(name: str, country: Optional[str] = None) -> str:
    """
    Narrow web dragnet for political biography, reforms, controversies.
    Extracts first 10 paragraphs from top SerpAPI results.
    """

    query_parts = [
        name,
        "politikan",
        "biografi",
        "profil",
        "skandal",
        "reforma"
    ]
    if country:
        query_parts.append(country)

    query = " ".join(query_parts)
    print(f"🔎 Scanning the web for politician: {query}...")

    search = GoogleSearch({
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
        "num": 3,
    })

    results = search.get_dict()
    raw_text = ""

    for result in results.get("organic_results", []):
        try:
            url = result["link"]
            print(f"   → Extracting: {url}")

            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            soup = BeautifulSoup(response.content, "html.parser")

            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs[:10])
            raw_text += f"\nSOURCE ({url}):\n{text}\n"

        except Exception:
            continue  # Fail-soft per URL

    return raw_text


# ============================================================
# 3. GEMINI 2.5 FLASH ANALYSIS
# ============================================================

def analyze_politician(name: str, country: Optional[str] = None) -> PoliticianProfile:
    """
    Main entrypoint for politician analytics:
    - Scrapes the web
    - Applies NOVARIC clinical neutrality constraints
    - Produces validated Pydantic output
    """

    raw_data = search_and_scrape_politician(name=name, country=country)

    # NEW GOOGLE GENERATIVE AI SDK
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

    json_schema_example = {
        "name": name,
        "archetype": "Reformer Technocrat",
        "bio_summary": "Neutral, 150–250 word narrative biography.",
        "genome": {
            "date_of_birth": "1969-03-15",
            "place_of_birth": "City, Region, Country",
            "country": country or "Albania",
            "party_affiliation": "Example Party",
            "ideology": "Centre-left social democrat",
            "first_elected_year": 2005,
            "current_role": "Member of Parliament",
            "key_policy_areas": [
                "Economy",
                "Judicial Reform",
                "EU Integration"
            ],
            "corruption_and_ethics_summary": (
                "Summarise any allegations, investigations, or clean record using "
                "strictly neutral language."
            ),
            "international_relations_summary": (
                "Summarise alignment with EU/US/NATO and relations with regional actors."
            ),
            "domestic_reputation_summary": (
                "Summarise how supporters and critics perceive the politician."
            ),
            "paragon_seed_scores": [65, 70, 60, 68, 62]
        }
    }

    prompt = f"""
You are NOVARIC's clinical political analyst.

Generate a structured, strictly neutral political profile for:
"{name}"

RAW MATERIAL (may include noise or bias):
{raw_data}

Rules:
- Be strictly factual and analytical.
- If data cannot be reliably inferred: return "Unknown".
- Never assert criminal guilt; only mention neutral statements like
  "alleged", "reported", "accused", or "investigated".
- Keep tone clinical, non-partisan, and non-defamatory.
- Keep dates approximate if needed.
- paragon_seed_scores: exactly 5 integers between 0–100.

Return ONLY valid JSON matching this exact structure:
{json.dumps(json_schema_example, indent=2)}
"""

    print("🧠 Running Gemini 2.5 Flash political profile analysis...")

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.25}
    )

    json_text = response.text.strip()

    if json_text.startswith("```"):
        json_text = json_text.strip("`").replace("json", "", 1).strip()

    return PoliticianProfile.model_validate_json(json_text)


# ============================================================
# 4. TEST RUN
# ============================================================

if __name__ == "__main__":
    target_name = "Edi Rama"
    target_country = "Albania"

    profile = analyze_politician(target_name, target_country)

    print("\n----- POLITICIAN DOSSIER -----")
    print(profile.model_dump_json(indent=2, ensure_ascii=False))
