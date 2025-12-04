from fastapi import APIRouter, HTTPException
from supabase import create_client
import os

router = APIRouter()

# --------------------------------------------------------
# Load correct environment variables
# MUST MATCH Cloud Run configuration exactly
# --------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise Exception("❌ Supabase environment variables are not set correctly in Cloud Run.")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@router.get("/visit")
def record_visit():
    """
    Calls the Supabase RPC increment_visit()
    and returns the updated global visitor count.
    """
    try:
        result = supabase.rpc("increment_visit", {}).execute()

        if result.error:
            raise HTTPException(status_code=500, detail=result.error.message)

        return {"count": result.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
