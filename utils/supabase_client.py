# utils/supabase_client.py
"""
Supabase client + REST helpers (Cloud Run–safe)

Goals:
- Never crash the app at import time (Cloud Run friendly).
- Provide a supabase-py Client when credentials are available.
- Preserve existing REST helper functions used across the codebase
  (supabase_upsert, supabase_insert, fetch_live_paragon_data, fetch_table).
"""

from __future__ import annotations

import os
from typing import Dict, Any, List, Optional

import requests

# ----------------------------------------------------
# Load environment variables (local dev only)
# ----------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # dotenv is optional; Cloud Run injects env vars directly.
    pass

# ----------------------------------------------------
# Environment configuration
# ----------------------------------------------------
SUPABASE_URL: str = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_SERVICE_ROLE_KEY: str = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
SUPABASE_ANON_KEY: str = (os.getenv("SUPABASE_ANON_KEY") or "").strip()

# Prefer SERVICE ROLE key for server-side writes
SUPABASE_KEY: str = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

# ----------------------------------------------------
# supabase-py client (preferred for new code paths)
# ----------------------------------------------------
supabase = None  # type: ignore

try:
    # supabase-py
    from supabase import create_client  # type: ignore

    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    # If supabase library is missing or misconfigured, we keep "supabase=None".
    supabase = None  # type: ignore

# ----------------------------------------------------
# Requests session (REST helpers)
# ----------------------------------------------------
_session = requests.Session()


def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


# ----------------------------------------------------
# INTERNAL: Ensure configuration is available
# (CRITICAL: do NOT raise at import time for Cloud Run)
# ----------------------------------------------------
def _ensure_config() -> None:
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL is missing. Set it in .env (local) or Cloud Run environment variables."
        )
    if not SUPABASE_KEY:
        raise RuntimeError(
            "No Supabase API key found. Set SUPABASE_SERVICE_ROLE_KEY (recommended) or SUPABASE_ANON_KEY."
        )


def _rest_url() -> str:
    _ensure_config()
    return f"{SUPABASE_URL.rstrip('/')}/rest/v1"


def _headers() -> Dict[str, str]:
    _ensure_config()
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


# ----------------------------------------------------
# INTERNAL GET helper
# ----------------------------------------------------
def _get(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{_rest_url()}/{path.lstrip('/')}"
    resp = _session.get(url, headers=_headers(), params=params, timeout=20)

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: Invalid Supabase API key (check service role key).")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase GET error {resp.status_code}: {resp.text}")

    data = resp.json()
    if isinstance(data, list):
        return data
    # Supabase REST should return arrays for SELECT; fallback safety:
    return [data]


# ----------------------------------------------------
# UPSERT helper (INSERT OR UPDATE) via REST
# ----------------------------------------------------
def supabase_upsert(
    table: str,
    records: List[Dict[str, Any]],
    conflict_col: str,
) -> Any:
    """
    Performs UPSERT (insert or update) on any table via Supabase REST.

    Example:
        supabase_upsert("paragon_scores", records, "politician_id")
    """
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("supabase_upsert: 'records' must be a non-empty list")

    url = f"{_rest_url()}/{table}"
    params = {"on_conflict": conflict_col}

    # Prefer "resolution=merge-duplicates" for upsert semantics
    headers = _headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"

    resp = _session.post(
        url,
        headers=headers,
        params=params,
        json=records,
        timeout=20,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase UPSERT failed [{resp.status_code}]: {resp.text}")

    try:
        return resp.json()
    except Exception:
        return {"status": "ok"}


# ----------------------------------------------------
# INSERT helper (used by Trend Engine) via REST
# ----------------------------------------------------
def supabase_insert(table: str, records: List[Dict[str, Any]]) -> Any:
    """
    Used for inserting history rows (e.g., paragon_trends).
    No upsert, no conflict handling.
    """
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("supabase_insert: 'records' must be a non-empty list")

    url = f"{_rest_url()}/{table}"

    headers = _headers()
    headers["Prefer"] = "return=representation"

    resp = _session.post(
        url,
        headers=headers,
        json=records,
        timeout=20,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase INSERT failed [{resp.status_code}]: {resp.text}")

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
        "order": "overall_score.desc",
    }
    return _get("paragon_scores", params)


# ----------------------------------------------------
# Generic table fetcher
# ----------------------------------------------------
def fetch_table(table: str, select: str = "*") -> List[Dict[str, Any]]:
    params = {"select": select}
    return _get(table, params)
