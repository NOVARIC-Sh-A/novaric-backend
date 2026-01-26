# services/supabase_admin.py
import os
from supabase import create_client, Client

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not _SUPABASE_URL or not _SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase_admin: Client = create_client(_SUPABASE_URL, _SUPABASE_SERVICE_ROLE_KEY)
