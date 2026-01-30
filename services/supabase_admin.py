from __future__ import annotations

from typing import Optional, TYPE_CHECKING

# Type-only import to avoid runtime issues when supabase isn't installed
if TYPE_CHECKING:  # pragma: no cover
    from supabase import Client as SupabaseClient  # type: ignore
else:  # pragma: no cover
    SupabaseClient = object  # type: ignore

# Singleton cache (Cloud Run friendly)
_supabase_admin: Optional["SupabaseClient"] = None


def get_supabase_admin() -> "SupabaseClient":
    """
    Returns a privileged Supabase client (ADMIN / service role).

    Cloud Run safe:
    - never raises at import time
    - raises only when actually called
    - reuses the shared Supabase client infrastructure
    - compatible with supabase>=2.0 and sb_secret_* keys
    """
    global _supabase_admin

    if _supabase_admin is not None:
        return _supabase_admin

    # Import here to avoid import-time side effects
    try:
        from utils.supabase_client import (
            SUPABASE_ADMIN_KEY,
            SUPABASE_URL,
            SUPABASE_CLIENT_INIT_ERROR,
        )
    except Exception as e:
        raise RuntimeError("Supabase client module unavailable") from e

    if not SUPABASE_URL or not SUPABASE_ADMIN_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SECRET_KEY")

    try:
        # Import lazily (Cloud Run safe)
        from supabase import create_client  # type: ignore
    except Exception as e:
        raise RuntimeError("supabase-py not installed or failed to import") from e

    try:
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)
        return _supabase_admin
    except Exception as e:
        # Preserve diagnostic context if available
        detail = SUPABASE_CLIENT_INIT_ERROR or str(e)
        raise RuntimeError(f"Failed to create Supabase admin client: {detail}") from e
