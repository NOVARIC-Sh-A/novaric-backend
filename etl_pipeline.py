import os
import feedparser
import statistics
from supabase import create_client, Client
from dotenv import load_dotenv

# --- 1. SETUP ---
# Load the passwords from the .env file
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: Missing keys. Did you create the .env file?")
    exit()

# Connect to the Database
supabase: Client = create_client(url, key)

# --- 2. CONFIGURATION ---
# The politicians we want to track (IDs must match your DB)
POLITICIANS = [
    {"id": 1, "name": "Edi Rama", "query": "Edi Rama Albania"},
    {"id": 2, "name": "Sali Berisha", "query": "Sali Berisha Albania"},
]

# --- 3. HELPER FUNCTIONS ---
def analyze_sentiment_mock(text):
    """
    Simple rule-based analysis. 
    (Later we will replace this with real AI/GPT)
    """
    text = text.lower()
    if any(x in text for x in ['success', 'win', 'good', 'agreement', 'growth']):
        return 0.8  # Positive
    elif any(x in text for x in ['scandal', 'fail', 'corruption', 'bad', 'protest']):
        return -0.6 # Negative
    return 0.1      # Neutral

# --- 4. MAIN PIPELINE ---
def run_pipeline():
    print("🚀 Starting NOVARIC Data Pipeline...")

    for politician in POLITICIANS:
        print(f"\n🔍 Searching news for: {politician['name']}...")
        
        # A. EXTRACT: Get news from Google RSS
        rss_url = f"https://news.google.com/rss/search?q={politician['query']}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        
        print(f"   Found {len(feed.entries)} articles.")
        
        recent_scores = []
        
        # We process the top 5 articles
        for entry in feed.entries[:5]: 
            
            # B. TRANSFORM: Calculate Sentiment
            sentiment = analyze_sentiment_mock(entry.title)
            
            # Prepare the data
            raw_data = {
                "politician_id": politician['id'],
                "source_type": "google_news",
                "content_summary": entry.title,
                "url": entry.link,
                "sentiment_score": sentiment
            }
            
            # C. LOAD: Send to Supabase
            try:
                supabase.table('raw_signals').insert(raw_data).execute()
                recent_scores.append(sentiment)
                print(f"   ✅ Saved Article: {entry.title[:40]}... (Score: {sentiment})")
            except Exception as e:
                print(f"   ⚠️ Error saving: {e}")

        # D. UPDATE SCORES
        if recent_scores:
            avg_sentiment = statistics.mean(recent_scores)
            
            # Math: Convert -1.0 to 1.0 range -> 0 to 100 range
            paragon_score = int(((avg_sentiment + 1) / 2) * 100)
            
            score_data = {
                "politician_id": politician['id'],
                "overall_score": paragon_score,
                "public_impact": paragon_score, 
                "integrity": 75, # Placeholder
                "leadership": 80 # Placeholder
            }
            
            # Save the score
            supabase.table('paragon_scores').insert(score_data).execute()
            print(f"   🏆 New Score for {politician['name']}: {paragon_score}/100")

    print("\n✅ Pipeline Finished.")

if __name__ == "__main__":
    run_pipeline()
