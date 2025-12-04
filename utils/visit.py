from fastapi import APIRouter, HTTPException
from supabase import create_client
import os

router = APIRouter()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = None

# Try connecting but DO NOT crash the app
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Visitor counter: Supabase connected")
    except Exception as e:
        print("⚠️ Visitor counter disabled:", e)
else:
    print("⚠️ Visitor counter disabled: missing env vars")


@router.get("/visit")
def record_visit():
    if not supabase:
        return {"count": 0}

    try:
        result = supabase.rpc("increment_visit", {}).execute()
        return {"count": result.data if result.data else 0}
    except Exception as e:
        print("⚠️ Visitor counter RPC failed:", e)
        return {"count": 0}
