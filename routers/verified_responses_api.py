from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException
from utils.supabase_client import supabase, is_supabase_configured

router = APIRouter(prefix="/api/v1", tags=["Verified Responses"])


def _require_supabase_or_503():
    if not is_supabase_configured() or supabase is None:
        raise HTTPException(status_code=503, detail="Supabase not configured")


@router.get("/verified-responses")
def list_verified_responses(
    topic: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    _require_supabase_or_503()

    qy = (
        supabase.table("verified_responses")
        .select("id,title,slug,summary,topic,published_at,updated_at,related_case_id")
        .eq("is_published", True)
        .order("published_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if topic:
        qy = qy.eq("topic", topic)

    res = qy.execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))

    return {"data": res.data or []}


@router.get("/verified-responses/{slug}")
def get_verified_response(slug: str):
    _require_supabase_or_503()

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
