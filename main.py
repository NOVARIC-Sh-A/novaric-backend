from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import feedparser
import os

# Dynamic data loader
from utils.data_loader import load_profiles_data

# === NEW IMPORT: PARAGON Analytics Routes ===
from paragon_api import router as paragon_router


# ================================================================
# FASTAPI APP CONFIGURATION
# ================================================================
app = FastAPI(
    title="NOVARIC Backend",
    description="Clinical scoring API for NOVARIC® PARAGON System",
    version="1.5.0",
)

# ================================================================
# CORS SETTINGS
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change to production domains later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# MODELS
# ================================================================
class AnalysisRequest(BaseModel):
    ids: List[str]
    category: str

class AnalysisResponseItem(BaseModel):
    id: str
    overallScore: int
    dimensions: Dict[str, int]

class AnalysisBatchResponse(BaseModel):
    analyses: List[AnalysisResponseItem]

class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    imageUrl: str = ""
    category: str
    timestamp: str


# ================================================================
# HEALTH CHECK ENDPOINT
# ================================================================
@app.get("/")
def root():
    """
    Standard health-check endpoint used by Cloud Run.
    Very lightweight and always succeeds.
    """
    return {
        "message": "NOVARIC PARAGON Engine is Online",
        "profiles_loaded": len(load_profiles_data()),
        "data_source": (
            "Supabase (Live)"
            if os.environ.get("USE_LIVE_DB") == "True"
            else "Local Mocks"
        ),
    }

# ================================================================
# PROFILES ENDPOINTS
# ================================================================
@app.get("/api/profiles")
def get_profiles():
    return load_profiles_data()

@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    profiles = load_profiles_data()
    profile = next((p for p in profiles if str(p["id"]) == profile_id), None)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


# ================================================================
# PROFILE ANALYSIS
# ================================================================
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    profiles = load_profiles_data()
    results = []

    for profile_id in request.ids:
        profile = next((p for p in profiles if str(p["id"]) == profile_id), None)
        if not profile:
            continue

        analysis = (
            profile.get("maragonAnalysis")
            or profile.get("paragonAnalysis")
            or []
        )

        dimensions_map = {
            item["dimension"]: item.get("score", 0)
            for item in analysis if item.get("dimension")
        }

        score_values = list(dimensions_map.values())
        overall = int(sum(score_values) / len(score_values)) if score_values else 0

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=overall,
                dimensions=dimensions_map,
            )
        )

    return AnalysisBatchResponse(analyses=results)


# ================================================================
# INTERNATIONAL NEWS FEEDS
# ================================================================
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://news.google.com/rss/search?q=site:reuters.com",
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "http://feeds.washingtonpost.com/rss/world",
    "https://time.com/feed",
    "https://apnews.com/feed/rss",
    "https://www.euronews.com/rss?format=mrss&level=theme&name=news",
    "https://rss.dw.com/xml/rss-en-world",
    "https://news.google.com/rss/search?q=site:apnews.com",
]

@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news():
    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            if feed.bozo and feed.status not in (200, 301):
                continue

            for entry in feed.entries[:5]:
                article_id = entry.get("id") or entry.get("link")
                if not article_id:
                    continue

                image_url = (
                    entry.media_content[0].get("url", "")
                    if "media_content" in entry and entry.media_content
                    else ""
                )

                articles.append(
                    NewsArticle(
                        id=str(article_id),
                        title=entry.get("title", "No Title"),
                        content=(entry.get("summary", "")[:300] + "..."),
                        imageUrl=image_url,
                        category="International",
                        timestamp=entry.get("published", "Unknown"),
                    )
                )

        except Exception as e:
            print(f"Feed error {url}: {e}")
            continue

    return articles


# ================================================================
# REGISTER PARAGON ANALYTICS ROUTES
# ================================================================
app.include_router(paragon_router)
