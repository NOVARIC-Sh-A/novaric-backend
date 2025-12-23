"""
Supabase client + REST helpers (Cloud Run–safe)

Goals:
- Never crash the app at import time (Cloud Run friendly).
- Provide a supabase-py Client when credentials are available.
- Provide robust REST helpers used across the codebase:
  - _get
  - supabase_insert
  - supabase_upsert  (with safe fallback when ON CONFLICT cannot be used)
  - fetch_live_paragon_data
  - fetch_table
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import requests

# ----------------------------------------------------
# Load environment variables (local dev only)
# ----------------------------------------------------
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
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
# supabase-py client (optional)
# ----------------------------------------------------
supabase = None  # type: ignore
try:
    from supabase import create_client  # type: ignore

    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    supabase = None  # type: ignore

# ----------------------------------------------------
# Requests session (REST helpers)
# ----------------------------------------------------
_session = requests.Session()


def is_supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


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


def _headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_config()
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


# ----------------------------------------------------
# INTERNAL: parse Supabase error JSON safely
# ----------------------------------------------------
def _try_parse_error(resp: requests.Response) -> Tuple[Optional[str], str]:
    """
    Returns (error_code, raw_text)
    """
    try:
        j = resp.json()
        if isinstance(j, dict):
            return (j.get("code"), resp.text)
    except Exception:
        pass
    return (None, resp.text)


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
    return [data]


# ----------------------------------------------------
# PATCH helper (used for manual upsert fallback)
# ----------------------------------------------------
def _patch(table: str, where_params: Dict[str, str], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{_rest_url()}/{table}"
    resp = _session.patch(
        url,
        headers=_headers(prefer="return=representation"),
        params=where_params,
        json=payload,
        timeout=20,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase PATCH failed [{resp.status_code}]: {resp.text}")

    try:
        data = resp.json()
        if isinstance(data, list):
            return data
        return [data]
    except Exception:
        return []


# ----------------------------------------------------
# INSERT helper via REST
# ----------------------------------------------------
def supabase_insert(table: str, records: List[Dict[str, Any]]) -> Any:
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("supabase_insert: 'records' must be a non-empty list")

    url = f"{_rest_url()}/{table}"
    resp = _session.post(
        url,
        headers=_headers(prefer="return=representation"),
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
# UPSERT helper (INSERT OR UPDATE) via REST
# with fallback when Postgres rejects ON CONFLICT
# ----------------------------------------------------
def supabase_upsert(
    table: str,
    records: List[Dict[str, Any]],
    conflict_col: str,
) -> Any:
    """
    Performs UPSERT (insert or update) on any table via Supabase REST.

    Primary method:
      POST /table?on_conflict=conflict_col
      Prefer: resolution=merge-duplicates

    Fallback method (when DB has no unique constraint on conflict_col):
      - PATCH /table?conflict_col=eq.<value>  (update)
      - if no row updated, POST insert

    This fallback keeps your API functional even if the DB constraint is missing,
    but the recommended fix is still adding a UNIQUE constraint in Postgres.
    """
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("supabase_upsert: 'records' must be a non-empty list")

    url = f"{_rest_url()}/{table}"
    params = {"on_conflict": conflict_col}
    headers = _headers(prefer="resolution=merge-duplicates,return=representation")

    resp = _session.post(url, headers=headers, params=params, json=records, timeout=20)

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code < 400:
        try:
            return resp.json()
        except Exception:
            return {"status": "ok"}

    # ---- Handle failure cases
    err_code, raw = _try_parse_error(resp)

    # 42P10 = "there is no unique or exclusion constraint matching the ON CONFLICT specification"
    if resp.status_code == 400 and err_code == "42P10":
        # Manual upsert: PATCH then INSERT
        out: List[Any] = []
        for rec in records:
            if conflict_col not in rec:
                raise RuntimeError(
                    f"supabase_upsert fallback failed: record missing conflict_col '{conflict_col}'"
                )

            key_val = rec[conflict_col]
            where = {conflict_col: f"eq.{key_val}"}

            # 1) try UPDATE
            updated = _patch(table, where, rec)

            if updated:
                out.extend(updated)
                continue

            # 2) if no row updated, INSERT
            inserted = supabase_insert(table, [rec])
            if isinstance(inserted, list):
                out.extend(inserted)
            else:
                out.append(inserted)

        return out

    raise RuntimeError(f"Supabase UPSERT failed [{resp.status_code}]: {raw}")


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
