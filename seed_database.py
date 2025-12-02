import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Import the clean data you just created
from mock_profiles import PROFILES 

# 1. Setup
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("❌ Error: Missing Supabase credentials in .env")
    exit()

supabase: Client = create_client(url, key)

def seed_politicians():
    print(f"🚀 Starting Database Seeding... Target: {len(PROFILES)} profiles.")
    
    success_count = 0
    
    for profile in PROFILES:
        # Prepare the data row matching your Supabase 'politicians' table
        # We assume the table has columns: id (auto), name, party, image_url, role
        
        # Extract Party from category string "Politikë (PS)" -> "PS"
        party_raw = profile.get('category', '')
        party = "Independent"
        if '(' in party_raw:
            party = party_raw.split('(')[1].replace(')', '')
            
        data_payload = {
            "name": profile['name'],
            "party": party,
            "role": profile['shortBio'],
            "image_url": profile['imageUrl'],
            # We map 'detailedBio' to a generic description or create a new column later
            # For now, we stick to the schema we built in Step 1
        }

        try:
            # Check if exists first to avoid duplicates (Upsert logic)
            existing = supabase.table('politicians').select("*").eq('name', profile['name']).execute()
            
            if existing.data:
                print(f"   ⚠️  Skipping {profile['name']} (Already exists)")
                # Optional: Update if you want to force sync
                # supabase.table('politicians').update(data_payload).eq('name', profile['name']).execute()
            else:
                supabase.table('politicians').insert(data_payload).execute()
                print(f"   ✅ Inserted: {profile['name']}")
                success_count += 1
                
        except Exception as e:
            print(f"   ❌ Failed to insert {profile['name']}: {e}")

    print(f"\n✨ Seeding Complete. Added {success_count} new profiles to Supabase.")

if __name__ == "__main__":
    seed_politicians()