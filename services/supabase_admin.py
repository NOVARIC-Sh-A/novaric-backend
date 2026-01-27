# services/supabase_admin.py
from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

# Type-only import to avoid runtime issues when supabase isn't installed
if TYPE_CHECKING:  # pragma: no cover
    from supabase import Client as SupabaseClient  # type: ignore
else:  # pragma: no cover
    SupabaseClient = object  # type: ignore

_supabase_admin: Optional["SupabaseClient"] = None


def get_supabase_admin() -> "SupabaseClient":
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

    try:
        # Import here to avoid import-time failures breaking server startup
        from supabase import create_client  # type: ignore
    except Exception as e:
        raise RuntimeError("supabase-py not installed or failed to import") from e

    _supabase_admin = create_client(url, key)
    return _supabase_admin
