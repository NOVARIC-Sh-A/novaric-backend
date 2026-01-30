from __future__ import annotations

from typing import Optional, Any, Dict, List


# ============================================================
# SUPABASE ADMIN CLIENT
# ============================================================
def db():
    """
    Returns a Supabase client initialized with service-role permissions.
    This must ONLY be used server-side.
    """
    from utils.supabase_client import get_supabase_admin  # local import prevents startup failures
    sb = get_supabase_admin()
    if not sb:
        raise RuntimeError("Supabase admin client is not configured (get_supabase_admin() returned None).")
    return sb


# ============================================================
# STORAGE HELPERS
# ============================================================
def upload_text(
    bucket: str,
    path: str,
    content: str,
    content_type: str = "text/html",
) -> str:
    """
    Uploads UTF-8 text content to Supabase Storage.
    Returns a simple URI string in the form: "{bucket}/{path}"
    """
    sb = db()
    sb.storage.from_(bucket).upload(
        path,
        content.encode("utf-8"),
        {"content-type": content_type, "upsert": True},
    )
    return f"{bucket}/{path}"


def upload_bytes(
    bucket: str,
    path: str,
    content: bytes,
    content_type: str,
) -> str:
    """
    Uploads raw bytes to Supabase Storage.
    Returns a simple URI string in the form: "{bucket}/{path}"
    """
    sb = db()
    sb.storage.from_(bucket).upload(
        path,
        content,
        {"content-type": content_type, "upsert": True},
    )
    return f"{bucket}/{path}"


# ============================================================
# CASE CRUD
# ============================================================
def upsert_case(
    vector_id: str,
    source_url: str,
    publisher: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Creates the forensic case if missing; otherwise returns existing.
    Uses vector_id as the business key.
    """
    sb = db()

    existing = (
        sb.table("forensic_cases")
        .select("*")
        .eq("vector_id", vector_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        # Optional: update metadata if new values provided
        current = existing.data[0]
        patch: Dict[str, Any] = {}
        if publisher and not current.get("publisher"):
            patch["publisher"] = publisher
        if title and not current.get("title"):
            patch["title"] = title
        if source_url and current.get("source_url") != source_url:
            patch["source_url"] = source_url

        if patch:
            updated = (
                sb.table("forensic_cases")
                .update(patch)
                .eq("id", current["id"])
                .execute()
            )
            if updated.data:
                return updated.data[0]
        return current

    ins = (
        sb.table("forensic_cases")
        .insert(
            {
                "vector_id": vector_id,
                "source_url": source_url,
                "publisher": publisher,
                "title": title,
                "status": "UNDER_FORENSIC_REVIEW",
            }
        )
        .execute()
    )
    if not ins.data:
        raise RuntimeError("Failed to insert forensic case (no data returned).")
    return ins.data[0]


def get_case_by_vector(vector_id: str) -> Optional[Dict[str, Any]]:
    sb = db()
    res = (
        sb.table("forensic_cases")
        .select("*")
        .eq("vector_id", vector_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def update_case(case_id: int, patch: Dict[str, Any]) -> None:
    if not patch:
        return
    sb = db()
    sb.table("forensic_cases").update(patch).eq("id", case_id).execute()


# ============================================================
# EVENTS (AUDIT TRAIL)
# ============================================================
def insert_event(
    case_id: int,
    event_type: str,
    *,
    actor: str = "system",
    snapshot_id: Optional[int] = None,
    analysis_id: Optional[int] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    sb = db()
    sb.table("forensic_events").insert(
        {
            "case_id": case_id,
            "snapshot_id": snapshot_id,
            "analysis_id": analysis_id,
            "event_type": event_type,
            "actor": actor,
            "payload": payload or {},
        }
    ).execute()


# ============================================================
# SNAPSHOTS
# ============================================================
def next_snapshot_seq(case_id: int) -> int:
    sb = db()
    res = (
        sb.table("forensic_snapshots")
        .select("snapshot_seq")
        .eq("case_id", case_id)
        .order("snapshot_seq", desc=True)
        .limit(1)
        .execute()
    )
    return (int(res.data[0]["snapshot_seq"]) + 1) if res.data else 1


def deactivate_previous_snapshots(case_id: int) -> None:
    """
    Ensures only one active snapshot per case.
    Safe to call even if none active.
    """
    sb = db()
    sb.table("forensic_snapshots").update({"is_active": False}).eq("case_id", case_id).eq(
        "is_active", True
    ).execute()


def insert_snapshot(
    *,
    case_id: int,
    snapshot_seq: int,
    canonical_url: str,
    http_status: Optional[int],
    fetch_meta: Dict[str, Any],
    content_hash_sha256: str,
    html_archive_uri: Optional[str],
    pdf_uri: Optional[str] = None,
    screenshots_uris: Optional[List[str]] = None,
    is_active: bool = True,
) -> Dict[str, Any]:
    sb = db()
    ins = (
        sb.table("forensic_snapshots")
        .insert(
            {
                "case_id": case_id,
                "snapshot_seq": snapshot_seq,
                "canonical_url": canonical_url,
                "http_status": http_status,
                "fetch_meta": fetch_meta or {},
                "content_hash_sha256": content_hash_sha256,
                "html_archive_uri": html_archive_uri,
                "pdf_uri": pdf_uri,
                "screenshots_uris": screenshots_uris or [],
                "is_active": is_active,
            }
        )
        .execute()
    )
    if not ins.data:
        raise RuntimeError("Failed to insert forensic snapshot (no data returned).")
    return ins.data[0]


def get_active_snapshot(case_id: int) -> Optional[Dict[str, Any]]:
    sb = db()
    res = (
        sb.table("forensic_snapshots")
        .select("*")
        .eq("case_id", case_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ============================================================
# ARTIFACTS
# ============================================================
def upsert_artifacts(
    *,
    snapshot_id: int,
    language: Optional[str],
    plain_text: str,
    text_hash_sha256: str,
    entities: Optional[List[Dict[str, Any]]] = None,
    quote_spans: Optional[List[Dict[str, Any]]] = None,
    claims: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    One row per snapshot_id (unique constraint).
    Uses upsert semantics via: select->update/insert (simple + reliable).
    """
    sb = db()

    existing = (
        sb.table("forensic_artifacts")
        .select("*")
        .eq("snapshot_id", snapshot_id)
        .limit(1)
        .execute()
    )
    payload = {
        "snapshot_id": snapshot_id,
        "language": language,
        "plain_text": plain_text,
        "text_hash_sha256": text_hash_sha256,
        "entities": entities or [],
        "quote_spans": quote_spans or [],
        "claims": claims or [],
    }

    if existing.data:
        upd = (
            sb.table("forensic_artifacts")
            .update(payload)
            .eq("snapshot_id", snapshot_id)
            .execute()
        )
        return upd.data[0] if upd.data else existing.data[0]

    ins = sb.table("forensic_artifacts").insert(payload).execute()
    if not ins.data:
        raise RuntimeError("Failed to insert forensic artifacts (no data returned).")
    return ins.data[0]


def get_artifacts(snapshot_id: int) -> Optional[Dict[str, Any]]:
    sb = db()
    res = (
        sb.table("forensic_artifacts")
        .select("*")
        .eq("snapshot_id", snapshot_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ============================================================
# ANALYSES
# ============================================================
def next_analysis_version(case_id: int) -> int:
    sb = db()
    res = (
        sb.table("forensic_analyses")
        .select("analysis_version")
        .eq("case_id", case_id)
        .order("analysis_version", desc=True)
        .limit(1)
        .execute()
    )
    return (int(res.data[0]["analysis_version"]) + 1) if res.data else 1


def insert_analysis(
    *,
    case_id: int,
    snapshot_id: int,
    analysis_version: int,
    engine_version: str,
    status: str,
    forensic_segments: List[Dict[str, Any]],
    evidence_points: List[Dict[str, Any]],
    fallacies: List[Dict[str, Any]],
    ethics_scorecard: List[Dict[str, Any]],
    rebuttal_ledger: List[Dict[str, Any]],
    verdict: Dict[str, Any],
    metrics: Dict[str, Any],
    created_by: str = "system",
) -> Dict[str, Any]:
    sb = db()
    ins = (
        sb.table("forensic_analyses")
        .insert(
            {
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "analysis_version": analysis_version,
                "engine_version": engine_version,
                "status": status,
                "forensic_segments": forensic_segments,
                "evidence_points": evidence_points,
                "fallacies": fallacies,
                "ethics_scorecard": ethics_scorecard,
                "rebuttal_ledger": rebuttal_ledger,
                "verdict": verdict,
                "metrics": metrics,
                "created_by": created_by,
            }
        )
        .execute()
    )
    if not ins.data:
        raise RuntimeError("Failed to insert forensic analysis (no data returned).")
    return ins.data[0]


def get_latest_analysis(case_id: int) -> Optional[Dict[str, Any]]:
    sb = db()
    res = (
        sb.table("forensic_analyses")
        .select("*")
        .eq("case_id", case_id)
        .order("analysis_version", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_analysis_by_version(case_id: int, analysis_version: int) -> Optional[Dict[str, Any]]:
    sb = db()
    res = (
        sb.table("forensic_analyses")
        .select("*")
        .eq("case_id", case_id)
        .eq("analysis_version", analysis_version)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


# ============================================================
# REPORTS
# ============================================================
def insert_report(
    *,
    case_id: int,
    analysis_id: int,
    report_type: str,
    uri: str,
    file_hash_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    sb = db()
    ins = (
        sb.table("forensic_reports")
        .insert(
            {
                "case_id": case_id,
                "analysis_id": analysis_id,
                "report_type": report_type,
                "uri": uri,
                "file_hash_sha256": file_hash_sha256,
            }
        )
        .execute()
    )
    if not ins.data:
        raise RuntimeError("Failed to insert forensic report (no data returned).")
    return ins.data[0]
