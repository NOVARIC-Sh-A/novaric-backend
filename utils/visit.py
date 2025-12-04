# novaric-backend/utils/visit.py
from fastapi import APIRouter
from supabase import create_client
import os

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = None

# Try to create the client, but DO NOT crash the app if something is wrong.
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Visitor counter: Supabase connected")
    except Exception as e:
        print("⚠️ Visitor counter disabled (Supabase error):", e)
        supabase = None
else:
    print("⚠️ Visitor counter disabled (missing SUPABASE env vars)")


@router.get("/visit")
def record_visit():
    """
    Return global visitor count using Supabase RPC.
    Fails gracefully with count=0 if anything goes wrong.
    """
    if not supabase:
        return {"count": 0}

    try:
        result = supabase.rpc("increment_visit", {}).execute()
        return {"count": result.data if result.data is not None else 0}
    except Exception as e:
        print("⚠️ Visitor counter RPC failed:", e)
        return {"count": 0}
