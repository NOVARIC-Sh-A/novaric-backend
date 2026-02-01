from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Literal

# Startup-safe import: never break router import in production
_FORENSIC_IMPORT_ERROR: Optional[str] = None

try:
    from services.forensic_service import (
        create_case_if_missing,
        list_cases,
        create_snapshot_for_case,
        run_analysis_for_case,
        get_forensic_page_payload,
        generate_pdf_for_case,
    )
except Exception as e:
    _FORENSIC_IMPORT_ERROR = str(e)
    create_case_if_missing = None  # type: ignore
    list_cases = None  # type: ignore
    create_snapshot_for_case = None  # type: ignore
    run_analysis_for_case = None  # type: ignore
    get_forensic_page_payload = None  # type: ignore
    generate_pdf_for_case = None  # type: ignore

router = APIRouter(prefix="/forensic", tags=["forensic"])


class CreateCaseReq(BaseModel):
    vectorId: str
    sourceUrl: str
    publisher: Optional[str] = None
    title: Optional[str] = None


def _ensure_forensic_ready():
    if _FORENSIC_IMPORT_ERROR:
        raise HTTPException(status_code=503, detail=f"Forensic module not ready: {_FORENSIC_IMPORT_ERROR}")
    if not all([
        create_case_if_missing,
        list_cases,
        create_snapshot_for_case,
        run_analysis_for_case,
        get_forensic_page_payload,
        generate_pdf_for_case
    ]):
        raise HTTPException(status_code=503, detail="Forensic module not ready")


@router.post("/cases")
def create_case(req: CreateCaseReq):
    _ensure_forensic_ready()
    return create_case_if_missing(req.vectorId, req.sourceUrl, req.publisher, req.title)


@router.get("/cases")
def get_cases(status: Optional[str] = None):
    _ensure_forensic_ready()
    return list_cases(status=status)


@router.post("/cases/{vector_id}/snapshots")
def snapshot_case(vector_id: str):
    _ensure_forensic_ready()
    return create_snapshot_for_case(vector_id)


@router.post("/cases/{vector_id}/analyses")
def analyze_case(vector_id: str):
    _ensure_forensic_ready()
    return run_analysis_for_case(vector_id)


@router.get("/cases/{vector_id}/forensic-page")
def forensic_page(vector_id: str, version: str = Query("latest")):
    _ensure_forensic_ready()
    return get_forensic_page_payload(vector_id, version)


@router.post("/cases/{vector_id}/pdf")
def generate_case_pdf(vector_id: str, version: str = Query("latest")):
    _ensure_forensic_ready()
    return generate_pdf_for_case(vector_id, version)
