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
    raise Exception("❌ SUPABASE_URL is missing. Add it to .env or Cloud Run env settings.")

# Prefer service-role (backend ETL writes)
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
if not SUPABASE_KEY:
    raise Exception("❌ No Supabase API key found (SERVICE_ROLE / ANON).")

# ----------------------------------------------------
# REST endpoint configuration
# ----------------------------------------------------
REST_URL = f"{SUPABASE_URL.rstrip('/')}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ----------------------------------------------------
# GET helper
# ----------------------------------------------------
def _get(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{REST_URL}/{path.lstrip('/')}"
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)

    if resp.status_code == 401:
        raise Exception("❌ Unauthorized: Invalid Supabase API Key")
    if resp.status_code >= 400:
        raise Exception(f"❌ Supabase GET error {resp.status_code}: {resp.text}")

    return resp.json()

# ----------------------------------------------------
# UPSERT helper (INSERT OR UPDATE)
# ----------------------------------------------------
def supabase_upsert(table: str, data: List[Dict[str, Any]], conflict_col: str):
    url = f"{REST_URL}/{table}"
    params = {"on_conflict": conflict_col}

    resp = requests.post(url, headers=HEADERS, params=params, json=data, timeout=20)

    if resp.status_code == 401:
        raise Exception("❌ Unauthorized: SERVICE_ROLE_KEY invalid or missing")

    if resp.status_code >= 400:
        raise Exception(f"❌ Supabase UPSERT failed [{resp.status_code}]: {resp.text}")

    try:
        return resp.json()
    except Exception:
        return {"status": "ok"}

# ----------------------------------------------------
# Fetch PARAGON scores + joined politician metadata
# ----------------------------------------------------
def fetch_live_paragon_data() -> List[Dict[str, Any]]:
    params = {
        "select": "*,politicians(*)",
        "order": "overall_score.desc",
    }
    return _get("paragon_scores", params)

# ----------------------------------------------------
# Generic table fetch
# ----------------------------------------------------
def fetch_table(table: str, select: str = "*") -> List[Dict[str, Any]]:
    params = {"select": select}
    return _get(table, params)
