from fastapi import APIRouter, Query, HTTPException
from utils.supabase_client import supabase

router = APIRouter(prefix="/api/v1", tags=["Fake News"])

@router.get("/case-studies")
def list_case_studies(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    verdict: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = (
        supabase.table("case_studies")
        .select("*")
        .eq("is_published", True)
        .order("audited_at", desc=True)
        .range(offset, offset + limit - 1)
    )

    if source:
        query = query.eq("source", source)
    if verdict:
        query = query.eq("verdict", verdict)
    if q:
        query = query.ilike("headline", f"%{q}%")

    res = query.execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))

    return {"data": res.data}


@router.get("/case-studies/{case_id}")
def get_case_study(case_id: str):
    cs = (
        supabase.table("case_studies")
        .select("*")
        .eq("id", case_id)
        .eq("is_published", True)
        .single()
        .execute()
    )

    if getattr(cs, "error", None) or not cs.data:
        raise HTTPException(status_code=404, detail="Not found")

    modules = (
        supabase.table("case_modules")
        .select("*")
        .eq("case_id", case_id)
        .order("sort_order", desc=False)
        .execute()
    )

    if getattr(modules, "error", None):
        raise HTTPException(status_code=500, detail=str(modules.error))

    return {"data": {**cs.data, "modules": modules.data}}
