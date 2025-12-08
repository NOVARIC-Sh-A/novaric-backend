import os
import requests
from bs4 import BeautifulSoup
from serpapi.google_search import GoogleSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

# ============================================================
# 1. LOAD API KEYS FROM ENVIRONMENT
# ============================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing from environment variables.")

if not SERPAPI_KEY:
    raise ValueError("SERPAPI_KEY is missing from environment variables.")

# ============================================================
# 2. DEFINE DATA MODELS (Your Media Genome Specification)
# ============================================================

class MediaGenome(BaseModel):
    date_of_birth: str = Field(description="YYYY-MM-DD or 'Unknown'")
    place_of_birth: str = Field(description="City, Country")
    career_start_year: int = Field(description="Year they started in media")

    evolutionary_status: str = Field(description="Ascending, Stagnant, Regressing, Compromised")
    top_rhetoric_shift: str = Field(description="e.g., 'From Investigative to Populist'")
    lethe_event: str = Field(description="Topic the personality avoids or survived")

    career_start_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] early career scores"
    )
    current_stats: List[int] = Field(
        description="[Readiness, Aptitude, Governance, Oversight, CSR] current scores"
    )

class ProfileData(BaseModel):
    name: str
    archetype: str = Field(description="Media archetype classification")
    bio_summary: str = Field(description="Objective summary of the person's background & career")
    genome: MediaGenome

# ============================================================
# 3. SEARCH & SCRAPE ENGINE — “THE DRAGNET”
# ============================================================

def search_and_scrape(query: str) -> str:
    print(f"\n🔎 Searching Google for: {query}")

    search = GoogleSearch({
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 5
    })

    results = search.get_dict()
    organic = results.get("organic_results", [])

    if not organic:
        print("⚠️ No search results found.")
        return ""

    raw_text = ""

    for result in organic[:5]:
        link = result.get("link")
        if not link:
            continue

        print(f"   --> Scraping: {link}")

        try:
            page = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")

            paras = soup.find_all("p")
            extracted = " ".join([p.get_text() for p in paras[:12]])

            raw_text += f"\nSOURCE ({link}):\n{extracted}\n"

        except Exception as e:
            print(f"   ⚠️ Could not scrape {link}: {e}")
            continue

    return raw_text.strip()

# ============================================================
# 4. GEMINI ANALYSIS ENGINE — “THE CLINICAL EXTRACTOR”
# ============================================================

def analyze_profile(person_name: str) -> ProfileData:
    """Runs the full enrichment pipeline: scrape → infer → produce Media Genome."""

    # STEP A — Gather raw external info
    scraped_data = search_and_scrape(f"{person_name} biografia gazetar politikan profile media")

    if not scraped_data:
        raise RuntimeError("No data scraped — cannot analyze profile.")

    # STEP B — Gemini LLM configuration
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2)
    parser = PydanticOutputParser(pydantic_object=ProfileData)

    prompt = PromptTemplate(
        template="""
You are **NORA**, the clinical analysis engine of NOVARIC® PARAGON.

Analyze the media/political personality: **{name}**  
using ONLY the factual evidence found in the text below.

-------------------------
SCRAPED RAW DATA:
{data}
-------------------------

Produce a **neutral, clinical, strictly factual intelligence report**.

RULES:
- Avoid all emotional, speculative, or defamatory content.
- Infer trends only from observed career evolution.
- When unknown, output "Unknown" instead of inventing details.

{format_instructions}
""",
        input_variables=["name", "data"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    print("\n🧠 Running Gemini Pro Analysis...")
    chain = prompt | llm | parser

    result: ProfileData = chain.invoke({
        "name": person_name,
        "data": scraped_data
    })

    print("✔ Gemini analysis complete.\n")

    return result

# ============================================================
# 5. OPTIONAL: RUN LOCALLY FOR TESTING
# ============================================================

if __name__ == "__main__":
    target = "Blendi Fevziu"  # example
    output = analyze_profile(target)

    print("\n================== DOSSIER ==================")
    print(output.json(indent=2))
