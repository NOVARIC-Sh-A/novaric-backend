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
