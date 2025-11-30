# main.py
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
# --------------------
import feedparser # ADDED: For RSS parsing
# --------------------

# NOTE: You need to ensure 'mock_profiles', 'utils.scoring', and 'PROFILES' 
# are available in your project structure for the existing code to work.

# Assuming the structure for imports based on the original code
from mock_profiles import PROFILES
from utils.scoring import generate_paragon_scores


app = FastAPI(
    title="NOVARIC Backend",
    description="Dynamic scoring API for NOVARIC® AI-Powered News",
    version="1.1.0",
)

# -------------------------------------------------------------
# CORS
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WARNING: Restrict this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Models
# -------------------------------------------------------------
class AnalysisRequest(BaseModel):
    ids: List[str]
    category: str


class AnalysisResponseItem(BaseModel):
    id: str
    overallScore: int
    dimensions: Dict[str, int]


class AnalysisBatchResponse(BaseModel):
    analyses: List[AnalysisResponseItem]

# ADDED: Pydantic model for the news endpoint
class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    imageUrl: str = ""
    category: str
    timestamp: str

# -------------------------------------------------------------
# Root Health Check
# -------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "NOVARIC Backend is running"}


# -------------------------------------------------------------
# Profiles Endpoints
# -------------------------------------------------------------
@app.get("/api/profiles")
def get_profiles():
    return PROFILES


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    for p in PROFILES:
        if p["id"] == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")


# -------------------------------------------------------------
# DYNAMIC ANALYSIS BATCH ENDPOINT
# -------------------------------------------------------------
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    results = []

    for profile_id in request.ids:
        profile = next((p for p in PROFILES if p["id"] == profile_id), None)

        if not profile:
            continue

        # 🔥 dynamic scoring HERE:
        analysis = generate_paragon_scores(
            name=profile["name"],
            category=request.category,
            zodiac=profile.get("zodiacSign", "Unknown")
        )

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=analysis["overall"],
                dimensions=analysis["dimensions"]
            )
        )

    return AnalysisBatchResponse(analyses=results)


# =============================================================
# === NEW NEWS ENDPOINT (Matching Frontend Service) ===
# =============================================================

# Top 10 International News Channel RSS Feeds
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml", 
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/worldNews", 
    "https://www.theguardian.com/world/rss", 
    "https://www.france24.com/en/rss",
    "http://feeds.washingtonpost.com/rss/world",
    "https://time.com/feed/world/",
    "https://apnews.com/feed/rss",
]

# Note: Using /api/v1/news as requested in the guide, 
# although your other endpoints use /api/
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news():
    articles = []

    for url in RSS_FEEDS:
        # Fetch the feed with a timeout
        feed = feedparser.parse(url, timeout=5) 
        
        if feed.bozo and feed.status != 200 and feed.status != 301:
            # print(f"Error parsing feed from {url}: {feed.bozo_exception}")
            continue

        for entry in feed.entries[:5]:  # Limit to 5 per source for faster response
            image_url = ''
            # Attempt to find an image in media namespace
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0].get('url', '')
            
            # Use 'link' as a fallback ID if 'id' is not present
            article_id = entry.get("id") or entry.get("link")
            
            if not article_id:
                # Skip if no reliable ID can be found
                continue

            articles.append(
                NewsArticle(
                    id=str(article_id),
                    title=entry.get("title", "No Title"),
                    content=entry.get("summary", ""),
                    imageUrl=image_url,
                    category="International", # Hardcode as per requirement
                    timestamp=entry.get("published", "Unknown"),
                )
            )

    return articles
