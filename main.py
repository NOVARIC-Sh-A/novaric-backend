# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import feedparser

# --- ARCHITECTURE CHANGE ---
# We import PROFILES from mock_profiles.
# NOTE: mock_profiles.py has already run the ParagonEngine logic at startup.
# So PROFILES contains the real, data-driven scores (Evidence + Logic).
from mock_profiles import PROFILES

app = FastAPI(
    title="NOVARIC Backend",
    description="Clinical scoring API for NOVARIC® PARAGON System",
    version="1.2.0",
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
    return {
        "message": "NOVARIC PARAGON Engine is Online", 
        "profiles_loaded": len(PROFILES)
    }

# -------------------------------------------------------------
# Profiles Endpoints
# -------------------------------------------------------------
@app.get("/api/profiles")
def get_profiles():
    # Returns the list of profiles (already clinically scored by Engine)
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
    """
    Returns the scores for a list of profile IDs.
    Instead of generating random numbers (Old Logic), this now pulls
    the CLINICAL SCORES calculated by the ParagonEngine in mock_profiles.py.
    """
    results = []

    for profile_id in request.ids:
        # Find the profile in our pre-calculated list
        profile = next((p for p in PROFILES if p["id"] == profile_id), None)

        if not profile:
            continue

        # Extract the score data from the profile structure
        # The Engine outputs a list of dictionaries: [{"dimension": "Name", "score": 80}, ...]
        # We need to format it into the Key-Value pair the Frontend expects for the Graph.
        
        dimensions_map = {}
        total_score = 0
        count = 0
        
        paragon_data = profile.get("paragonAnalysis", [])
        
        # If it's a media profile using Maragon, handle that
        if not paragon_data and "maragonAnalysis" in profile:
            paragon_data = profile.get("maragonAnalysis", [])

        for item in paragon_data:
            dim_name = item.get("dimension")
            score = item.get("score", 0)
            dimensions_map[dim_name] = score
            total_score += score
            count += 1
        
        # Calculate strict average
        overall = int(total_score / count) if count > 0 else 0

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=overall,
                dimensions=dimensions_map
            )
        )

    return AnalysisBatchResponse(analyses=results)


# =============================================================
# === NEWS ENDPOINT ===
# =============================================================

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

@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news():
    articles = []

    for url in RSS_FEEDS:
        try:
            # Fetch the feed with a timeout (handled by library or socket defaults)
            feed = feedparser.parse(url) 
            
            if feed.bozo and feed.status != 200 and feed.status != 301:
                continue

            for entry in feed.entries[:5]:  # Limit to 5 per source
                image_url = ''
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url', '')
                
                article_id = entry.get("id") or entry.get("link")
                
                if not article_id:
                    continue

                articles.append(
                    NewsArticle(
                        id=str(article_id),
                        title=entry.get("title", "No Title"),
                        content=entry.get("summary", "")[:300] + "...", # Truncate long summaries
                        imageUrl=image_url,
                        category="International",
                        timestamp=entry.get("published", "Unknown"),
                    )
                )
        except Exception as e:
            print(f"Error parsing feed {url}: {e}")
            continue

    return articles
