import os
import feedparser
import statistics
from supabase import create_client, Client
from dotenv import load_dotenv

# IMPORT THE METHODOLOGY LOGIC
from methodology import calculate_paragon_score, calculate_pip_status, normalize_score

# 1. SETUP
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: Keys missing.")
    exit()

supabase: Client = create_client(url, key)

# 2. CONFIGURATION (Politicians)
POLITICIANS = [
    {"id": 1, "name": "Edi Rama", "query": "Edi Rama Albania"},
    {"id": 2, "name": "Sali Berisha", "query": "Sali Berisha Albania"},
]

# 3. AI SIMULATION (To be replaced by GPT-4 later)
def analyze_article_dimensions(text):
    """
    Analyzes text and returns scores for the PARAGON dimensions.
    """
    text = text.lower()
    
    # Mock Analysis Logic based on keywords
    scores = {
        "political_engagement": 50, # Neutral start
        "integrity": 50,
        "governance": 50,
        "communication": 50,
        "influence": 50
    }
    
    # Simple Keyword Scoring (Temporary until GPT-4)
    if "corruption" in text or "spak" in text or "scandal" in text:
        scores['integrity'] = 20 # Low score
    if "eu" in text or "integration" in text or "investment" in text:
        scores['political_engagement'] = 80
    if "speech" in text or "interview" in text:
        scores['communication'] = 75
    if "decree" in text or "law" in text:
        scores['governance'] = 70

    return scores

# 4. MAIN PIPELINE
def run_pipeline():
    print("🚀 Starting PARAGON® Analytical Engine...")

    for politician in POLITICIANS:
        print(f"\n👤 Processing: {politician['name']}...")
        
        # A. EXTRACT (News)
        rss_url = f"https://news.google.com/rss/search?q={politician['query']}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(rss_url)
        
        daily_metrics = {
            "political_engagement": [],
            "integrity": [],
            "governance": [],
            "communication": [],
            "influence": []
        }
        
        print(f"   Found {len(feed.entries)} articles.")

        # B. TRANSFORM (Apply Dimensions)
        for entry in feed.entries[:5]:
            # Get dimension scores for this article
            article_scores = analyze_article_dimensions(entry.title)
            
            # Save Raw Signal
            raw_data = {
                "politician_id": politician['id'],
                "source_type": "google_news",
                "content_summary": entry.title,
                "url": entry.link,
                # Store the average of dimensions as a proxy for sentiment
                "sentiment_score": (sum(article_scores.values()) / 5) / 100 
            }
            supabase.table('raw_signals').insert(raw_data).execute()
            
            # Aggregate data
            for key, val in article_scores.items():
                daily_metrics[key].append(val)

        # C. COMPUTE PARAGON SCORE
        if daily_metrics['integrity']: # If we have data
            
            # 1. Average the daily inputs
            avg_inputs = {
                "political_engagement": statistics.mean(daily_metrics['political_engagement']),
                "integrity": statistics.mean(daily_metrics['integrity']),
                "governance": statistics.mean(daily_metrics['governance']),
                "communication": statistics.mean(daily_metrics['communication']),
                "influence": statistics.mean(daily_metrics['influence']),
            }

            # 2. Apply Weighted Formula (Methodology)
            final_paragon_score = calculate_paragon_score(avg_inputs)
            
            # 3. Calculate PIP (Integrity Matrix)
            # Using 'integrity' as Behavioral Risk (inverted) and 'influence' as Structural Vulnerability
            structural = avg_inputs['influence'] 
            behavioral_risk = 100 - avg_inputs['integrity'] # Low integrity = High risk
            
            pip_result = calculate_pip_status(structural, behavioral_risk)

            # D. LOAD (Save to DB)
            score_entry = {
                "politician_id": politician['id'],
                "overall_score": final_paragon_score,
                "leadership": int(avg_inputs['governance']),
                "integrity": int(avg_inputs['integrity']),
                "public_impact": int(avg_inputs['communication'])
            }
            
            supabase.table('paragon_scores').insert(score_entry).execute()
            
            print(f"   🏆 PARAGON Score: {final_paragon_score}")
            print(f"   🛡️ PIP Status: {pip_result['title']} ({pip_result['status']})")

    print("\n✅ Analysis Complete.")

if __name__ == "__main__":
    run_pipeline()
