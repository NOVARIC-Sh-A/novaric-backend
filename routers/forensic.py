from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/forensic", tags=["forensic"])

@router.get("/health")
def health():
    return {"ok": True, "module": "forensic"}
