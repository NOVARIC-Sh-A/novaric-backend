# services/supabase_admin.py
from __future__ import annotations
import os
from typing import Optional

try:
    from supabase import create_client, Client  # type: ignore
except Exception:  # pragma: no cover
    create_client = None  # type: ignore
    Client = object  # type: ignore

_supabase_admin: Optional["Client"] = None

def get_supabase_admin() -> "Client":
    """
    Cloud Run safe:
    - does not raise at import time
    - raises only when actually called
    """
    global _supabase_admin

    if _supabase_admin is not None:
        return _supabase_admin

    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()

    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

    if create_client is None:
        raise RuntimeError("supabase-py not installed or failed to import")

    _supabase_admin = create_client(url, key)
    return _supabase_admin
