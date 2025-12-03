# utils/supabase_client.py
import os
from supabase import create_client, Client
from typing import List, Dict
from dotenv import load_dotenv # NEW: Explicitly load environment variables

# --- Initialization ---
load_dotenv() # Load variables from .env file

# Determine which key to use (API Read Key or Service Role Key)
SUPABASE_URL: str = os.environ.get("SUPABASE_URL") or os.environ.get("REACT_APP_SUPABASE_URL")
# Use the Anonymous Key for read-only API access (safer)
SUPABASE_KEY: str = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("REACT_APP_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # If anonymous key is missing, fall back to service key for backend read/write
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not SUPABASE_KEY:
        raise Exception("Supabase credentials not found in environment variables.")

SUPABASE: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_live_paragon_data() -> List[Dict]:
    """
    Fetches and joins profile and paragon data from Supabase.
    Throws a generic Exception on error, which the caller must handle.
    """
    try:
        # Note: 'politicians' is assumed to be the name of your secondary table.
        # The 'select' uses PostgREST syntax for foreign key joins:
        response = SUPABASE.table('paragon_scores').select('*, politicians(*)').execute()
        
        if response.error:
            # Throw a generic Exception that FastAPI can catch later
            raise Exception(f"Supabase query failed: {response.error.message}")
            
        return response.data
    
    except Exception as e:
        # Re-throw the error for the calling FastAPI function to handle
        raise Exception(f"Supabase connection or query error: {e}")