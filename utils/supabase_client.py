# utils/supabase_client.py
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
import requests

# --- Load environment variables ---
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL is not set in environment variables (.env).")

# Prefer service role on backend (for writes); fallback to anon for read-only
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
if not SUPABASE_KEY:
    raise Exception(
        "Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY found in environment."
    )

REST_URL = f"{SUPABASE_URL.rstrip('/')}/rest/v1"

DEFAULT_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def _get(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Internal helper to perform GET requests to Supabase REST."""
    url = f"{REST_URL}/{path.lstrip('/')}"
    response = requests.get(url, headers=DEFAULT_HEADERS, params=params, timeout=15)

    # Raise HTTP errors (404, 500, etc.)
    response.raise_for_status()
    return response.json()


def fetch_live_paragon_data() -> List[Dict[str, Any]]:
    """
    Fetch joined PARAGON scores + politician data from Supabase.
    Equivalent to: select * from paragon_scores join politicians
    """
    params = {
        "select": "*,politicians(*)",
        # You can add filters here, e.g.: "order": "overall_score.desc"
    }

    try:
        data = _get("paragon_scores", params)
        return data
    except Exception as e:
        raise Exception(f"Supabase REST query failed: {e}") from e


def fetch_table(table: str, select: str = "*") -> List[Dict[str, Any]]:
    """
    Generic helper to fetch any table.
    Example: fetch_table("politicians")
    """
    params = {"select": select}
    try:
        return _get(table, params)
    except Exception as e:
        raise Exception(f"Supabase REST query on '{table}' failed: {e}") from e
