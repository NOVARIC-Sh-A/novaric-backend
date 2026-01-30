from services.forensic_repo import (
    upsert_case, get_case_by_vector, insert_event,
    next_snapshot_seq, deactivate_previous_snapshots, db, upload_text
)
from services.forensic_snapshot import snapshot_payload
from utils.forensic_hash import sha256_text

def create_case_if_missing(vector_id: str, source_url: str, publisher=None, title=None):
    case = upsert_case(vector_id, source_url, publisher, title)
    insert_event(case["id"], "CASE_CREATED", payload={"vector_id": vector_id, "source_url": source_url})
    return {"caseId": case["id"], "vectorId": case["vector_id"], "status": case["status"]}

def list_cases(status=None):
    q = db().table("forensic_cases").select("*").order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return res.data

def create_snapshot_for_case(vector_id: str):
    case = get_case_by_vector(vector_id)
    if not case:
        raise Exception("Case not found")

    seq = next_snapshot_seq(case["id"])
    payload = snapshot_payload(case["source_url"])

    # upload html
    html_path = f"{vector_id}/snap_{seq}/source.html"
    html_path = f"{vector_id}/snap_{int(seq):04d}/source.html"
    html_uri = upload_text("forensic-snapshots", html_path, payload["html"], "text/html")

    # create snapshot row (deactivate old active first)
    deactivate_previous_snapshots(case["id"])

    snap_ins = db().table("forensic_snapshots").insert({
        "case_id": case["id"],
        "snapshot_seq": seq,
        "canonical_url": case["source_url"],
        "http_status": payload["http_status"],
        "fetch_meta": payload["fetch_meta"],
        "content_hash_sha256": payload["content_hash_sha256"],
        "html_archive_uri": html_uri,
        "pdf_uri": None,
        "screenshots_uris": [],
        "is_active": True
    }).execute()
    snapshot = snap_ins.data[0]

    # create artifacts (plaintext now, claims later)
    text_hash = sha256_text(payload["plain_text"])
    db().table("forensic_artifacts").insert({
        "snapshot_id": snapshot["id"],
        "language": "sq",
        "plain_text": payload["plain_text"],
        "text_hash_sha256": text_hash,
        "entities": [],
        "quote_spans": [],
        "claims": []
    }).execute()

    # set active snapshot on case
    db().table("forensic_cases").update({"active_snapshot_id": snapshot["id"], "status": "SNAPSHOTTED"}).eq("id", case["id"]).execute()

    insert_event(case["id"], "SNAPSHOT_CREATED", snapshot_id=snapshot["id"], payload={
        "snapshot_seq": seq,
        "content_hash_sha256": payload["content_hash_sha256"],
        "html_uri": html_uri
    })

    return {"snapshotId": snapshot["id"], "snapshotSeq": seq, "contentHashSha256": payload["content_hash_sha256"]}

def run_analysis_for_case(vector_id: str):
    case = get_case_by_vector(vector_id)
    if not case:
        raise Exception("Case not found")

    # load active snapshot
    snap_res = (
        db()
        .table("forensic_snapshots")
        .select("*")
        .eq("case_id", case["id"])
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    snapshot = (snap_res.data or [None])[0]
    if not snapshot:
        raise Exception("No active snapshot")

    # next analysis version
    ver_res = (
        db()
        .table("forensic_analyses")
        .select("analysis_version")
        .eq("case_id", case["id"])
        .order("analysis_version", desc=True)
        .limit(1)
        .execute()
    )
    next_ver = (int(ver_res.data[0]["analysis_version"]) + 1) if (ver_res.data or []) else 1

    # minimal analysis payload (keeps your pipeline runnable now)
    analysis_payload = {
        "case_id": case["id"],
        "snapshot_id": snapshot["id"],
        "analysis_version": next_ver,
        "engine_version": "CIDA_v2.4",
        "status": "COMPLETED",
        "forensic_segments": [],
        "evidence_points": [],
        "fallacies": [],
        "ethics_scorecard": [],
        "rebuttal_ledger": [],
        "verdict": {},
        "metrics": {},
        "created_by": "system",
    }

    ins = db().table("forensic_analyses").insert(analysis_payload).execute()
    analysis = ins.data[0] if (ins.data or []) else None
    if not analysis:
        raise Exception("Analysis insert failed")

    # update case status
    db().table("forensic_cases").update({"status": "ANALYZED"}).eq("id", case["id"]).execute()

    insert_event(case["id"], "ANALYSIS_COMPLETED", snapshot_id=snapshot["id"], analysis_id=analysis["id"], payload={
        "analysis_version": next_ver,
        "engine_version": "CIDA_v2.4",
    })

    return {"analysisId": analysis["id"], "analysisVersion": next_ver, "status": analysis.get("status")}

def get_forensic_page_payload(vector_id: str, version: str = "latest"):
    case = get_case_by_vector(vector_id)
    if not case:
        return {"data": None}

    snap_res = (
        db()
        .table("forensic_snapshots")
        .select("*")
        .eq("case_id", case["id"])
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    snapshot = (snap_res.data or [None])[0]

    artifacts = None
    if snapshot:
        art_res = (
            db()
            .table("forensic_artifacts")
            .select("*")
            .eq("snapshot_id", snapshot["id"])
            .limit(1)
            .execute()
        )
        artifacts = (art_res.data or [None])[0]

    analysis = None
    if version == "latest":
        an_res = (
            db()
            .table("forensic_analyses")
            .select("*")
            .eq("case_id", case["id"])
            .order("analysis_version", desc=True)
            .limit(1)
            .execute()
        )
        analysis = (an_res.data or [None])[0]
    else:
        try:
            v = int(version)
        except Exception:
            v = 0
        if v > 0:
            an_res = (
                db()
                .table("forensic_analyses")
                .select("*")
                .eq("case_id", case["id"])
                .eq("analysis_version", v)
                .limit(1)
                .execute()
            )
            analysis = (an_res.data or [None])[0]

    def _sign(uri: str, expires_in: int = 600) -> str:
        if not uri or "/" not in uri:
            return ""
        bucket, path = uri.split("/", 1)
        try:
            r = db().storage.from_(bucket).create_signed_url(path, expires_in)
            if isinstance(r, dict) and r.get("signedURL"):
                return r["signedURL"]
            if hasattr(r, "get") and r.get("signedURL"):
                return r.get("signedURL")  # type: ignore
            return ""
        except Exception:
            return ""

    if snapshot and isinstance(snapshot, dict):
        html_uri = snapshot.get("html_archive_uri") or ""
        pdf_uri = snapshot.get("pdf_uri") or ""
        shots = snapshot.get("screenshots_uris") or []

        snapshot["html_archive_signed_url"] = _sign(str(html_uri), 600) if html_uri else ""
        snapshot["pdf_signed_url"] = _sign(str(pdf_uri), 600) if pdf_uri else ""
        snapshot["screenshots_signed_urls"] = [_sign(str(x), 600) for x in (shots or [])] if isinstance(shots, list) else []

    return {
        "data": {
            "case": case,
            "snapshot": snapshot,
            "artifacts": artifacts,
            "analysis": analysis,
        }
    }
