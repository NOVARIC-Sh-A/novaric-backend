import os
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from dotenv import load_dotenv

# LangChain (v0.3 compatible)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from pydantic import BaseModel, Field
from typing import List

# Load API keys
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY missing in .env")
if not SERPAPI_KEY:
    raise ValueError("❌ SERPAPI_KEY missing in .env")


# ============================================================
#   1. DATA MODELS
# ============================================================
class MediaGenome(BaseModel):
    date_of_birth: str = Field(description="YYYY-MM-DD or 'Unknown'")
    place_of_birth: str = Field(description="City, Country")
    career_start_year: int = Field(description="Year started in media")

    evolutionary_status: str = Field(
        description="Ascending, Stagnant, Regressing, Compromised"
    )
    top_rhetoric_shift: str = Field(description="Short phrase summarizing rhetoric evolution")
    lethe_event: str = Field(description="A topic the personality avoids recently")

    career_start_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] initial values (0–100)"
    )
    current_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] current values (0–100)"
    )


class ProfileData(BaseModel):
    name: str
    archetype: str
    bio_summary: str
    genome: MediaGenome


# ============================================================
#   2. SEARCH & SCRAPE (Dragnet)
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
            extracted = " ".join([p.get_text() for p in paragraphs[:10]])

            raw_text += f"\nSOURCE ({url}):\n{extracted}\n"

        except Exception as e:
            print(f"   ⚠️ Error extracting {url}: {e}")
            continue

    return raw_text


# ============================================================
#   3. GEMINI ADVANCED CLINICAL ANALYSIS
# ============================================================
def analyze_profile(name: str):
    raw_data = search_and_scrape(f"{name} biografia gazetari media polemika")

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",       # FIXED MODEL
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2
    )

    parser = PydanticOutputParser(pydantic_object=ProfileData)

    prompt = PromptTemplate(
        template="""
You are NOVARIC's clinical media analyst.

Analyze the media personality: {target_name}

RAW GATHERED MATERIAL:
{raw_data}

INSTRUCTIONS:
1. Determine their evolutionary_status.
2. Identify a clear top_rhetoric_shift.
3. Identify one Lethe Event (topic they avoid).
4. Estimate MARAGON stats (start vs. now).
5. Produce a clinical, neutral, non-emotional summary.
6. Output MUST follow the required JSON schema.

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
#   4. DIRECT TEST RUN
# ============================================================
if __name__ == "__main__":
    target = "Blendi Fevziu"
    profile = analyze_profile(target)

    print("\n===== DOSSIER GENERATED =====")
    print(profile.json(indent=2))
