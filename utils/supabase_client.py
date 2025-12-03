# utils/supabase_client.py
import os
from supabase import create_client, Client

# Initialize Supabase client
supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise Exception("Supabase credentials not found in environment variables.")
    
SUPABASE: Client = create_client(supabase_url, supabase_key)

def fetch_live_paragon_data() -> List[Dict]:
    """Fetches and joins profile and paragon data from Supabase."""
    # Assuming 'paragon_scores' table has a foreign key to 'politicians'
    # This query fetches all columns from 'paragon_scores' and all columns 
    # from the joined 'politicians' table.
    
    # NOTE: You may need to adjust the query based on your exact schema.
    response = SUPABASE.table('paragon_scores').select('*, politicians(*)').execute()
    
    if response.error:
        raise HTTPException(status_code=500, detail=f"Supabase error: {response.error.message}")
        
    return response.data
