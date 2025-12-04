from fastapi import APIRouter, HTTPException
from supabase import create_client
import os

router = APIRouter()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

@router.get("/visit")
def record_visit():
    try:
        result = supabase.rpc("increment_visit").execute()

        if result.error:
            raise HTTPException(status_code=500, detail=result.error.message)

        return {"total_visits": result.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
