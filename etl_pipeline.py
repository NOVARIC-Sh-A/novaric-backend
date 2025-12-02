import os
import feedparser
import urllib.parse  # <--- NEW IMPORT
from supabase import create_client, Client
from dotenv import load_dotenv

# IMPORT HYBRID MODULES
from schemas import AI_Extraction_Output
from methodology import calculate_hybrid_score, calculate_pip_status 

# 1. SETUP
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase keys in .env")
    exit()

supabase: Client = create_client(url, key)

# FETCH TARGETS FROM DB
response = supabase.table('politicians').select("id, name").execute()
POLITICIANS = []
for row in response.data:
    POLITICIANS.append({
        "id": row['id'],
        "name": row['name'],
        "query": row['name'] # Default query is the name
    })

print(f"📋 Loaded {len(POLITICIANS)} politicians from database to monitor.")

# 2. AI MOCK (To be replaced by GPT-4)
def mock_ai_extractor(title):
    title = title.lower()
    
    # Logic to simulate AI reading
    is_corruption = "scandal" in title or "spak" in title or "corruption" in title
    is_eu = "eu" in title or "agreement" in title
    is_protest = "protest" in title or "clash" in title

    sentiment = 0.0
    if "success" in title or "win" in title: sentiment = 0.8
    elif "fail" in title or "bad" in title: sentiment = -0.6
    
    return AI_Extraction_Output(
        is_political_event=True,
        sentiment_score=sentiment,
        primary_topic="Politics",
        has_corruption_allegation=is_corruption,
        has_legislative_action="law" in title,
        has_international_endorsement=is_eu,
        has_public_outcry=is_protest,
        brief_summary=f"Summary of: {title}"
    )

# 3. MAIN PIPELINE
def run_pipeline():
    print("🚀 Starting PARAGON® Hybrid Pipeline...")
    
    for pol in POLITICIANS:
        print(f"\n🔍 Processing {pol['name']}...")
        
        # --- FIX: URL ENCODING ---
        # We handle spaces properly here (e.g., "Edi Rama" -> "Edi%20Rama")
        search_term = f"{pol['query']} Albania"
        encoded_search = urllib.parse.quote(search_term)
        
        rss_url = f"https://news.google.com/rss/search?q={encoded_search}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        
        extracted_data_list = []
        
        # A. EXTRACT & TRANSFORM (AI Layer)
        print(f"   Found {len(feed.entries)} articles.")
        
        for entry in feed.entries[:5]:
            ai_data = mock_ai_extractor(entry.title)
            extracted_data_list.append(ai_data)
            
            # Save Raw Signal
            supabase.table('raw_signals').insert({
                "politician_id": pol['id'],
                "source_type": "google_news",
                "content_summary": ai_data.brief_summary,
                "sentiment_score": ai_data.sentiment_score,
                "url": entry.link
            }).execute()

        # B. COMPUTE SCORES (Methodology Layer)
        result = calculate_hybrid_score(extracted_data_list)
        
        if result:
            breakdown = result['breakdown']
            
            # C. DIAGNOSE (PIP Matrix Layer)
            pip_status = calculate_pip_status(
                structural_vulnerability=breakdown['influence'],
                behavioral_risk=(100 - breakdown['integrity'])
            )

            # D. LOAD (Database Layer)
            supabase.table('paragon_scores').insert({
                "politician_id": pol['id'],
                "overall_score": result['overall'],
                "leadership": breakdown['governance'],
                "integrity": breakdown['integrity'],
                "public_impact": breakdown['communication']
            }).execute()
            
            print(f"   🏆 Overall Score: {result['overall']}")
            print(f"   🛡️ Integrity: {breakdown['integrity']} | PIP Status: {pip_status['title']}")

if __name__ == "__main__":
    run_pipeline()