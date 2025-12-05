# utils/supabase_client.py

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
import requests

# ----------------------------------------------------
# Load environment variables
# ----------------------------------------------------
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    raise Exception("❌ SUPABASE_URL is missing. Add it to .env or Cloud Run environment settings.")

# Prefer SERVICE-ROLE key (required for ETL writes)
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
if not SUPABASE_KEY:
    raise Exception("❌ No Supabase API key found (SERVICE_ROLE_KEY or ANON_KEY).")

# ----------------------------------------------------
# REST endpoint config
# ----------------------------------------------------
REST_URL = f"{SUPABASE_URL.rstrip('/')}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ----------------------------------------------------
# INTERNAL GET helper
# ----------------------------------------------------
def _get(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{REST_URL}/{path.lstrip('/')}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)

    if resp.status_code == 401:
        raise Exception("❌ Unauthorized: Invalid Supabase API key")

    if resp.status_code >= 400:
        raise Exception(f"❌ Supabase GET error {resp.status_code}: {resp.text}")

    return resp.json()

# ----------------------------------------------------
# UPSERT helper (INSERT OR UPDATE)
# ----------------------------------------------------
def supabase_upsert(
    table: str,
    records: List[Dict[str, Any]],
    conflict_col: str
):
    """
    Performs UPSERT (insert or update) on any table via Supabase REST.

    Example:
        supabase_upsert("paragon_scores", records, "politician_id")
    """

    if not isinstance(records, list) or len(records) == 0:
        raise Exception("❌ supabase_upsert: 'records' must be a non-empty list")

    url = f"{REST_URL}/{table}"
    params = {"on_conflict": conflict_col}

    resp = requests.post(
        url,
        headers=HEADERS,
        params=params,
        json=records,
        timeout=20
    )

    if resp.status_code == 401:
        raise Exception("❌ Unauthorized: SERVICE_ROLE_KEY invalid or missing")

    if resp.status_code >= 400:
        raise Exception(f"❌ Supabase UPSERT failed [{resp.status_code}]: {resp.text}")

    try:
        return resp.json()
    except Exception:
        return {"status": "ok"}

# ----------------------------------------------------
# INSERT helper (used by Trend Engine)
# ----------------------------------------------------
def supabase_insert(table: str, records: List[Dict[str, Any]]):
    """
    Used for inserting history rows (e.g., paragon_trends).
    No upsert, no conflict handling.
    """

    if not isinstance(records, list) or len(records) == 0:
        raise Exception("❌ supabase_insert: 'records' must be a non-empty list")

    url = f"{REST_URL}/{table}"

    resp = requests.post(
        url,
        headers=HEADERS,
        json=records,
        timeout=20
    )

    if resp.status_code == 401:
        raise Exception("❌ Unauthorized: SERVICE_ROLE_KEY invalid or missing")

    if resp.status_code >= 400:
        raise Exception(f"❌ Supabase INSERT failed [{resp.status_code}]: {resp.text}")

    try:
        return resp.json()
    except Exception:
        return {"status": "ok"}

# ----------------------------------------------------
# Fetch PARAGON + joined politician data
# ----------------------------------------------------
def fetch_live_paragon_data() -> List[Dict[str, Any]]:
    params = {
        "select": "*,politicians(*)",
        "order": "overall_score.desc"
    }
    return _get("paragon_scores", params)

# ----------------------------------------------------
# Generic table fetcher
# ----------------------------------------------------
def fetch_table(table: str, select: str = "*") -> List[Dict[str, Any]]:
    params = {"select": select}
    return _get(table, params)
