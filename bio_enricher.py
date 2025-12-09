import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from pydantic import BaseModel, Field
from typing import List

# Load .env file
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# ============================================================
#   1. DATA MODELS
# ============================================================
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


# ============================================================
#   2. SEARCH + SCRAPE (Dragnet)
# ============================================================
def search_and_scrape(query):
    print(f"🔎 Scanning the web for: {query}...")

    search = GoogleSearch({
        "q": query,
        "api_key": SERPAPI_KEY,
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


# ============================================================
#   3. GEMINI CLINICAL ANALYSIS
# ============================================================
def analyze_profile(name: str):
    raw_data = search_and_scrape(f"{name} biografia gazetari media polemika")

    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3
    )

    parser = PydanticOutputParser(pydantic_object=ProfileData)

    prompt = PromptTemplate(
        template="""
You are NOVARIC's clinical media analyst.
Analyze the media personality: {target_name}

RAW MATERIAL BELOW:
{raw_data}

INSTRUCTIONS:
1. Determine evolutionary_status.
2. Identify rhetoric shift.
3. Identify a Lethe Event.
4. Estimate early vs. current MARAGON stats.
5. Be analytical, neutral, clinical.

{format_instructions}
        """,
        input_variables=["target_name", "raw_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | llm | parser

    print("🧠 Running Gemini analysis...")
    result = chain.invoke({"target_name": name, "raw_data": raw_data})

    return result


# ============================================================
#   4. TEST RUN
# ============================================================
if __name__ == "__main__":
    target = "Blendi Fevziu"
    profile = analyze_profile(target)

    print("\n----- DOSSIER -----")
    print(profile.json(indent=2))
