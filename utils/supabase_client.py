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

Extra reliability:
- Expose why supabase-py client creation failed (SUPABASE_CLIENT_INIT_ERROR).
- Provide an always-available REST fallback that mimics the subset of supabase-py
  used by your routers (.table().select().eq().order().range().single().execute()).

NEW (required for your current production key format sb_secret_* / sb_publishable_*):
- Always-available Supabase Storage REST upload helpers:
  - storage_upload_bytes
  - storage_upload_text
- Split keys:
  - SUPABASE_READ_KEY  (prefer anon)
  - SUPABASE_ADMIN_KEY (service role only; required for writes/storage)
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
# NOTE:
# We keep the original env names, but also tolerate common misconfigurations
# (e.g. truncated variable name in Cloud Run: SUPABASE_SERVICE_ROLE_KE).
def _env_first(*names: str) -> str:
    for n in names:
        v = (os.getenv(n) or "").strip()
        if v:
            return v
    return ""


SUPABASE_URL: str = _env_first("SUPABASE_URL")

# service role key can be misnamed in some deployments; tolerate safely
SUPABASE_SECRET_KEY: str = _env_first(
    "SUPABASE_SECRET_KEY",
    "SUPABASE_SERVICE_ROLE_KE",  # common truncation typo
    "SUPABASE_SERVICE_KEY",  # occasional alternative naming
)

SUPABASE_PUBLISHABLE_KEY: str = _env_first(
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_KEY",  # some stacks export anon as SUPABASE_KEY
)

# NEW:
# - READ key: prefer anon if available (least privilege); otherwise fall back to service role
# - ADMIN key: service role ONLY (hard requirement for writes/storage)
SUPABASE_READ_KEY: str = SUPABASE_PUBLISHABLE_KEY or SUPABASE_SECRET_KEY
SUPABASE_ADMIN_KEY: str = SUPABASE_SECRET_KEY

# Back-compat (some call-sites expect SUPABASE_KEY)
# We point SUPABASE_KEY to READ key (least privilege by default).
SUPABASE_KEY: str = SUPABASE_READ_KEY

# ----------------------------------------------------
# Supabase URL sanity checks (prevents "YOUR_SUPABASE_URL" failures)
# ----------------------------------------------------
def _looks_like_placeholder(url: str) -> bool:
    u = (url or "").strip().lower()
    return (
        not u
        or u
        in {
            "your_supabase_url",
            "supabase_url",
            "http://your_supabase_url",
            "https://your_supabase_url",
        }
        or "your_supabase_url" in u
    )


def _has_scheme(url: str) -> bool:
    u = (url or "").strip().lower()
    return u.startswith("http://") or u.startswith("https://")


def _validate_supabase_url(url: str) -> str:
    """
    Keeps behavior Cloud Run–safe (no import-time crash),
    but prevents invalid request URLs like "YOUR_SUPABASE_URL/rest/v1/...".
    """
    u = (url or "").strip()
    if not u:
        return ""
    if _looks_like_placeholder(u):
        return ""
    if not _has_scheme(u):
        # treat as invalid (avoid requests "No scheme supplied")
        return ""
    return u.rstrip("/")


# Normalize once
SUPABASE_URL = _validate_supabase_url(SUPABASE_URL)

# ----------------------------------------------------
# Requests session (REST helpers)
# ----------------------------------------------------
_session = requests.Session()

# Optional: slightly more resilient networking without changing call-sites.
try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    _retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST", "PATCH"}),
        raise_on_status=False,
    )
    _adapter = HTTPAdapter(max_retries=_retry, pool_connections=10, pool_maxsize=10)
    _session.mount("https://", _adapter)
    _session.mount("http://", _adapter)
except Exception:
    # If urllib3 Retry is unavailable for any reason, continue without retries.
    pass


def is_supabase_configured() -> bool:
    """
    True only when URL is valid and at least one key is present.
    """
    return bool(SUPABASE_URL and (SUPABASE_READ_KEY or SUPABASE_ADMIN_KEY))


def _ensure_config() -> None:
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL is missing or invalid. "
            "Set SUPABASE_URL to something like: https://<project-ref>.supabase.co"
        )
    if not (SUPABASE_READ_KEY or SUPABASE_ADMIN_KEY):
        raise RuntimeError(
            "No Supabase API key found. Set SUPABASE_SECRET_KEY (recommended) "
            "or SUPABASE_PUBLISHABLE_KEY."
        )


def _rest_url() -> str:
    _ensure_config()
    # SUPABASE_URL is already rstrip("/") in _validate_supabase_url
    return f"{SUPABASE_URL}/rest/v1"


def _storage_url() -> str:
    _ensure_config()
    return f"{SUPABASE_URL}/storage/v1"


def _headers(*, prefer: Optional[str] = None, key: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, str]:
    _ensure_config()

    # Supabase supports both:
    # - Legacy JWT keys: "eyJhbGciOi..."
    # - New API keys: "sb_publishable_..." / "sb_secret_..."
    #
    # PostgREST expects apikey and Authorization Bearer.
    key = (key or SUPABASE_READ_KEY or "").strip()

    if not key:
        raise RuntimeError("Supabase key missing for this operation.")

    h: Dict[str, str] = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }

    # Default JSON content-type for PostgREST operations
    if content_type:
        h["Content-Type"] = content_type
    else:
        h["Content-Type"] = "application/json"

    if prefer:
        h["Prefer"] = prefer
    return h


# ----------------------------------------------------
# INTERNAL: parse Supabase error JSON safely
# ----------------------------------------------------
def _try_parse_error(resp: requests.Response) -> Tuple[Optional[str], str]:
    """
    Returns (error_code, raw_text).
    """
    try:
        j = resp.json()
        if isinstance(j, dict):
            return (j.get("code"), resp.text)
    except Exception:
        pass
    return (None, resp.text)


# ----------------------------------------------------
# INTERNAL: safer json parsing for list/object responses
# ----------------------------------------------------
def _try_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return None


# ----------------------------------------------------
# INTERNAL: normalize Supabase REST JSON response to List[Dict]
# ----------------------------------------------------
def _normalize_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        return [data]
    return []


# ----------------------------------------------------
# INTERNAL GET helper
# ----------------------------------------------------
def _get(path: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    url = f"{_rest_url()}/{path.lstrip('/')}"
    resp = _session.get(url, headers=_headers(key=SUPABASE_READ_KEY), params=params, timeout=20)

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: Invalid Supabase API key (check anon/service role key).")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase GET error {resp.status_code}: {resp.text}")

    return _normalize_list(_try_json(resp))


# ----------------------------------------------------
# PATCH helper (used for manual upsert fallback)
# ----------------------------------------------------
def _patch(table: str, where_params: Dict[str, str], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not SUPABASE_ADMIN_KEY:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    url = f"{_rest_url()}/{table}"
    resp = _session.patch(
        url,
        headers=_headers(prefer="return=representation", key=SUPABASE_ADMIN_KEY),
        params=where_params,
        json=payload,
        timeout=20,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase PATCH failed [{resp.status_code}]: {resp.text}")

    return _normalize_list(_try_json(resp))


# ----------------------------------------------------
# INSERT helper via REST
# ----------------------------------------------------
def supabase_insert(table: str, records: List[Dict[str, Any]]) -> Any:
    if not isinstance(records, list) or len(records) == 0:
        raise ValueError("supabase_insert: 'records' must be a non-empty list")

    if not SUPABASE_ADMIN_KEY:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    url = f"{_rest_url()}/{table}"
    resp = _session.post(
        url,
        headers=_headers(prefer="return=representation", key=SUPABASE_ADMIN_KEY),
        json=records,
        timeout=20,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase INSERT failed [{resp.status_code}]: {resp.text}")

    data = _try_json(resp)
    return data if data is not None else {"status": "ok"}


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

    if not SUPABASE_ADMIN_KEY:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    url = f"{_rest_url()}/{table}"
    params = {"on_conflict": conflict_col}
    headers = _headers(prefer="resolution=merge-duplicates,return=representation", key=SUPABASE_ADMIN_KEY)

    resp = _session.post(url, headers=headers, params=params, json=records, timeout=20)

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing.")

    if resp.status_code < 400:
        data = _try_json(resp)
        return data if data is not None else {"status": "ok"}

    # ---- Handle failure cases
    err_code, raw = _try_parse_error(resp)

    # 42P10 = "there is no unique or exclusion constraint matching the ON CONFLICT specification"
    if resp.status_code == 400 and err_code == "42P10":
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
# Supabase Storage REST upload helpers (sb_secret_ compatible)
# ----------------------------------------------------
def storage_upload_bytes(bucket: str, path: str, content: bytes, content_type: str) -> str:
    """
    Upload bytes to Supabase Storage using REST.
    Requires SUPABASE_SECRET_KEY (ADMIN key) in production for private buckets.
    Returns "bucket/path" (stable internal URI format).
    """
    if not SUPABASE_ADMIN_KEY:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing (Storage).")

    url = f"{_storage_url()}/object/{bucket}/{path.lstrip('/')}"
    resp = _session.post(
        url,
        headers={
            **_headers(key=SUPABASE_ADMIN_KEY, content_type=content_type),
            "x-upsert": "true",
        },
        data=content,
        timeout=30,
    )

    if resp.status_code == 401:
        raise RuntimeError("Unauthorized: SERVICE_ROLE_KEY invalid or missing (Storage).")

    if resp.status_code >= 400:
        raise RuntimeError(f"Storage upload failed [{resp.status_code}]: {resp.text}")

    return f"{bucket}/{path.lstrip('/')}"


def storage_upload_text(bucket: str, path: str, content: str, content_type: str = "text/html") -> str:
    return storage_upload_bytes(bucket, path, (content or "").encode("utf-8"), content_type)


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
    return _get(table, {"select": select})


# ----------------------------------------------------
# REST fallback that mimics the subset of supabase-py we use
# (extended to cover insert/update/upsert used by forensic services)
# ----------------------------------------------------
class _RestQuery:
    def __init__(self, table: str):
        self._table = table
        self._select = "*"
        self._filters: list[tuple[str, str, str]] = []  # (col, op, val)
        self._order: tuple[str, bool] | None = None  # (col, desc)
        self._range: tuple[int, int] | None = None
        self._single = False

        # write ops
        self._op: str = "select"  # select | insert | update | upsert
        self._payload: Any = None
        self._upsert_conflict: Optional[str] = None

    def select(self, cols: str):
        self._op = "select"
        self._select = cols or "*"
        return self

    def insert(self, payload: Any):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: Dict[str, Any]):
        self._op = "update"
        self._payload = payload
        return self

    def upsert(self, payload: Any, *, on_conflict: Optional[str] = None):
        self._op = "upsert"
        self._payload = payload
        self._upsert_conflict = on_conflict
        return self

    def eq(self, col: str, val: object):
        self._filters.append((col, "eq", str(val)))
        return self

    def ilike(self, col: str, pattern: str):
        self._filters.append((col, "ilike", pattern))
        return self

    def in_(self, col: str, values: list[str]):
        # PostgREST expects: col=in.(a,b,c)
        joined = ",".join([str(v) for v in values])
        self._filters.append((col, "in", f"({joined})"))
        return self

    def order(self, col: str, desc: bool = False):
        self._order = (col, bool(desc))
        return self

    def range(self, start: int, end: int):
        self._range = (int(start), int(end))
        return self

    def limit(self, n: int):
        # emulate limit by range(0, n-1) if range not set
        if self._range is None:
            self._range = (0, int(n) - 1)
        return self

    def single(self):
        self._single = True
        return self

    def _build_params(self) -> dict[str, object]:
        params: dict[str, object] = {"select": self._select}

        for col, op, val in self._filters:
            if op == "eq":
                params[col] = f"eq.{val}"
            elif op == "ilike":
                params[col] = f"ilike.{val}"
            elif op == "in":
                params[col] = f"in.{val}"

        if self._order:
            col, desc = self._order
            params["order"] = f"{col}.{'desc' if desc else 'asc'}"

        # Supabase REST supports offset + limit
        if self._range:
            start, end = self._range
            params["offset"] = str(start)
            params["limit"] = str(max(0, end - start + 1))

        return params

    def execute(self):
        try:
            if self._op == "select":
                params = self._build_params()
                data = _get(self._table, params)
                if self._single:
                    item = data[0] if data else None
                    return type("Resp", (), {"data": item, "error": None})
                return type("Resp", (), {"data": data, "error": None})

            if self._op == "insert":
                payload = self._payload
                records: List[Dict[str, Any]]
                if isinstance(payload, list):
                    records = payload
                elif isinstance(payload, dict):
                    records = [payload]
                else:
                    raise RuntimeError("insert payload must be dict or list[dict]")
                data = supabase_insert(self._table, records)
                return type("Resp", (), {"data": data, "error": None})

            if self._op == "update":
                if not isinstance(self._payload, dict):
                    raise RuntimeError("update payload must be dict")
                where_params: Dict[str, str] = {}
                for col, op, val in self._filters:
                    if op == "eq":
                        where_params[col] = f"eq.{val}"
                    elif op == "ilike":
                        where_params[col] = f"ilike.{val}"
                    elif op == "in":
                        where_params[col] = f"in.{val}"
                data = _patch(self._table, where_params, self._payload)
                return type("Resp", (), {"data": data, "error": None})

            if self._op == "upsert":
                payload = self._payload
                conflict_col = (self._upsert_conflict or "").strip()
                if not conflict_col:
                    raise RuntimeError("upsert requires on_conflict=<column>")
                records2: List[Dict[str, Any]]
                if isinstance(payload, list):
                    records2 = payload
                elif isinstance(payload, dict):
                    records2 = [payload]
                else:
                    raise RuntimeError("upsert payload must be dict or list[dict]")
                data = supabase_upsert(self._table, records2, conflict_col)
                return type("Resp", (), {"data": data, "error": None})

            raise RuntimeError(f"Unsupported operation: {self._op}")
        except Exception as e:
            return type("Resp", (), {"data": None, "error": str(e)})


class _RestSupabase:
    def table(self, name: str):
        return _RestQuery(name)


# ----------------------------------------------------
# supabase-py client (optional) + init diagnostics
# ----------------------------------------------------
SUPABASE_CLIENT_INIT_ERROR: Optional[str] = None


def _is_jwt_like(key: str) -> bool:
    """
    Legacy Supabase keys are JWT-like (three dot-separated parts).
    New sb_secret/sb_publishable keys are NOT JWT-like and may break supabase-py
    depending on the installed version.
    """
    k = (key or "").strip()
    return k.count(".") == 2


def _create_supabase_py_client():
    """
    Try to create supabase-py client. Never raises.
    Sets SUPABASE_CLIENT_INIT_ERROR on failure.
    """
    global SUPABASE_CLIENT_INIT_ERROR
    SUPABASE_CLIENT_INIT_ERROR = None

    if not (SUPABASE_URL and SUPABASE_KEY):
        SUPABASE_CLIENT_INIT_ERROR = "SUPABASE_URL or SUPABASE_KEY missing/invalid"
        return None

    # Avoid noisy failures when using new non-JWT keys (sb_secret_/sb_publishable_)
    if not _is_jwt_like(SUPABASE_KEY):
        SUPABASE_CLIENT_INIT_ERROR = "create_client skipped: key is not JWT-like (likely sb_secret/sb_publishable)"
        return None

    try:
        from supabase import create_client  # type: ignore
    except Exception as e:
        SUPABASE_CLIENT_INIT_ERROR = f"import supabase failed: {e}"
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        SUPABASE_CLIENT_INIT_ERROR = f"create_client failed: {e}"
        return None


# This is what your routers import and use: `from utils.supabase_client import supabase`
# We guarantee:
# - None if NOT configured
# - supabase-py client if possible
# - REST fallback if configured but supabase-py fails
_supabase_py = _create_supabase_py_client()
supabase = None  # type: ignore
if is_supabase_configured():
    supabase = _supabase_py if _supabase_py is not None else _RestSupabase()
else:
    supabase = None  # type: ignore


def get_supabase_client():
    """
    Returns a usable client (supabase-py OR REST fallback) when configured.
    If not configured, returns None.

    Also exposes SUPABASE_CLIENT_INIT_ERROR for diagnostics.
    """
    if not is_supabase_configured():
        return None
    return supabase


# Back-compat: some services expect db() / get_supabase_admin()
def db():
    return get_supabase_client()


def get_supabase_admin():
    return get_supabase_client()
