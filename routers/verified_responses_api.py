from fastapi import APIRouter, Query, HTTPException
from utils.supabase_client import supabase

router = APIRouter(prefix="/api/v1", tags=["Verified Responses"])

@router.get("/verified-responses")
def list_verified_responses(
    topic: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    q = (
        supabase.table("verified_responses")
        .select("id,title,slug,summary,topic,published_at,updated_at,related_case_id")
        .eq("is_published", True)
        .order("published_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if topic:
        q = q.eq("topic", topic)

    res = q.execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))
    return {"data": res.data}


@router.get("/verified-responses/{slug}")
def get_verified_response(slug: str):
    res = (
        supabase.table("verified_responses")
        .select("*")
        .eq("slug", slug)
        .eq("is_published", True)
        .single()
        .execute()
    )
    if getattr(res, "error", None) or not res.data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"data": res.data}
