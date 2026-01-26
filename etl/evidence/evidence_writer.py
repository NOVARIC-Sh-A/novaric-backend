# etl/evidence/evidence_writer.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from etl.evidence.contracts import EvidenceItem
from etl.evidence.hash_utils import canonicalize_url, sha256_text, url_hash
from utils.supabase_client import supabase_upsert


def build_evidence_row(
    ev: EvidenceItem,
    *,
    run_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convert an EvidenceItem into a Supabase-ready row for public.evidence_items.

    Requires in DB:
      - evidence_items.dedupe_key TEXT UNIQUE
    """
    url_c = canonicalize_url(ev.url)
    content = (ev.raw_text or ev.snippet or "").strip()

    uhash = url_hash(url_c)
    dedupe_key = f"{ev.source_key}:{uhash}"

    return {
        # Stable upsert key (single-column conflict target)
        "dedupe_key": dedupe_key,
        # Identity resolution (may be null)
        "politician_id": ev.politician_id,
        # Provenance
        "source_key": ev.source_key,
        "run_id": run_id,
        # Dedupe helpers
        "url": url_c,
        "url_hash": uhash,
        "content_hash": sha256_text(content[:20000]),  # cap for stable hashing
        # Content metadata
        "title": (ev.title or "").strip() or None,
        "published_at": ev.published_at,
        "content_type": ev.content_type,
        "language": ev.language,
        # Extracted text
        "snippet": (ev.snippet or "").strip()[:600] or None,
        "raw_text": (ev.raw_text or "").strip()[:20000] or None,
        # Enrichment
        "entities": ev.entities or {},
        "topics": ev.topics or [],
        "signals": ev.signals or {},
        "extraction_confidence": float(ev.extraction_confidence or 0.6),
    }


def write_evidence_batch(
    evidence: List[EvidenceItem],
    *,
    run_id: Optional[int],
    batch_size: int = 200,
) -> int:
    """
    Upsert evidence into public.evidence_items using dedupe_key.

    Notes:
    - Ensures stable idempotency across re-runs.
    - Requires a UNIQUE constraint / unique index on evidence_items.dedupe_key.
    """
    if not evidence:
        return 0

    rows = [build_evidence_row(ev, run_id=run_id) for ev in evidence]
    total = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase_upsert("evidence_items", batch, conflict_col="dedupe_key")
        total += len(batch)

    return total
