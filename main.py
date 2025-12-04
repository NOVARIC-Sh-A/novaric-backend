# main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import feedparser
import os

# ### NEW ADDITION: Supabase Import (Replaces Redis) ###
from supabase import create_client, Client

# ================================================================
# LIVE / MOCK DYNAMIC LOADING
# ================================================================
from utils.data_loader import load_profiles_data

app = FastAPI(
    title="NOVARIC Backend",
    description="Clinical scoring API for NOVARIC® PARAGON System",
    version="1.3.2", # Bumped version for Supabase Integration
)

# -------------------------------------------------------------
# ### NEW ADDITION: Supabase Connection Setup ###
# -------------------------------------------------------------
# Connects to your existing Supabase project.
# Ensure these ENV variables are set in Cloud Run.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Use Service Role or Anon Key

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase for Visitor Counting")
    except Exception as e:
        print(f"⚠️ Warning: Could not connect to Supabase: {e}")
else:
    print("⚠️ Warning: SUPABASE_URL or SUPABASE_KEY not set.")

# -------------------------------------------------------------
# CORS
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # In production, replace "*" with your specific Frontend URL
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# MODELS
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
# ROOT HEALTH CHECK
# -------------------------------------------------------------
@app.get("/")
def root():
    data_source = (
        "Supabase (Live)" 
        if os.environ.get("USE_LIVE_DB") == "True" 
        else "Local Mocks"
    )
    
    profiles = load_profiles_data()
    return {
        "message": "NOVARIC PARAGON Engine is Online",
        "profiles_loaded": len(profiles),
        "data_source": data_source,
        "visitor_counter_status": "Active" if supabase else "Inactive"
    }

# -------------------------------------------------------------
# ### NEW ADDITION: Visitor Counter Endpoint (Supabase RPC) ###
# -------------------------------------------------------------
@app.get("/api/visit")
def track_visit(request: Request):
    """
    Increments visitor count atomically using Supabase RPC.
    This removes the need for Redis.
    """
    if not supabase:
        return {"count": 0, "error": "Database unavailable"}

    try:
        # Call the Stored Procedure 'increment_visitor' on Supabase
        # This function handles the +1 math safely inside the database
        response = supabase.rpc('increment_visitor', {}).execute()
        
        # supabase-py returns the result in response.data
        new_count = response.data 
        
        return {"count": new_count if new_count is not None else 0}
            
    except Exception as e:
        print(f"Visitor Error: {e}")
        # Fail gracefully so the website doesn't crash
        return {"count": 0}

# -------------------------------------------------------------
# PROFILES ENDPOINTS (LIVE per request)
# -------------------------------------------------------------
@app.get("/api/profiles")
def get_profiles():
    """Always fetches LIVE data on each request."""
    profiles = load_profiles_data()
    return profiles

@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    """Fetch one profile dynamically."""
    profiles = load_profiles_data()
    for p in profiles:
        if str(p["id"]) == profile_id:
            return p
    raise HTTPException(status_code=404, detail="Profile not found")

# -------------------------------------------------------------
# DYNAMIC ANALYSIS ENDPOINT
# -------------------------------------------------------------
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    profiles = load_profiles_data()
    results = []

    for profile_id in request.ids:
        profile = next(
            (p for p in profiles if str(p["id"]) == profile_id),
            None
        )

        if not profile:
            continue

        dimensions_map = {}
        total_score = 0
        count = 0

        analysis = (
            profile.get("maragonAnalysis") 
            or profile.get("paragonAnalysis") 
            or []
        )

        for item in analysis:
            dim_name = item.get("dimension")
            score = item.get("score", 0)
            if dim_name and score is not None:
                dimensions_map[dim_name] = score
                total_score += score
                count += 1

        overall = int(total_score / count) if count > 0 else 0

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=overall,
                dimensions=dimensions_map,
            )
        )

    return AnalysisBatchResponse(analyses=results)

# -------------------------------------------------------------
# INTERNATIONAL NEWS ENDPOINT
# -------------------------------------------------------------
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
                image_url = (
                    entry.media_content[0].get("url", "")
                    if "media_content" in entry and entry.media_content
                    else ""
                )
                article_id = entry.get("id") or entry.get("link")
                if not article_id:
                    continue

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
            print(f"Error parsing feed {url}: {e}")
            continue

    return articles