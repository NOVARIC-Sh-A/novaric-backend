from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Literal

from services.forensic_service import (
    create_case_if_missing,
    list_cases,
    create_snapshot_for_case,
    run_analysis_for_case,
    get_forensic_page_payload,
)

router = APIRouter(prefix="/forensic", tags=["forensic"])

class CreateCaseReq(BaseModel):
    vectorId: str
    sourceUrl: str
    publisher: Optional[str] = None
    title: Optional[str] = None

@router.post("/cases")
def create_case(req: CreateCaseReq):
    return create_case_if_missing(req.vectorId, req.sourceUrl, req.publisher, req.title)

@router.get("/cases")
def get_cases(status: Optional[str] = None):
    return list_cases(status=status)

@router.post("/cases/{vector_id}/snapshots")
def snapshot_case(vector_id: str):
    return create_snapshot_for_case(vector_id)

@router.post("/cases/{vector_id}/analyses")
def analyze_case(vector_id: str):
    return run_analysis_for_case(vector_id)

@router.get("/cases/{vector_id}/forensic-page")
def forensic_page(vector_id: str, version: str = Query("latest")):
    return get_forensic_page_payload(vector_id, version)
