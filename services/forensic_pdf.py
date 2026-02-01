# services/forensic_pdf.py
"""
NOVARIC® Forensic Engine — CIDA PDF Generator (ReportLab)

Purpose
-------
Generate a clean, readable PDF report from a CIDA audit payload / forensic page payload.

Design principles
-----------------
- Pure Python, no browser dependencies (uses ReportLab).
- Defensive against missing fields and mixed transcript structures.
- Produces bytes, so caller can upload to Supabase Storage.

Expected inputs
---------------
You can pass either:
A) The raw audit JSON returned by run_cida_audit(), plus optional case metadata; OR
B) The already-normalized page payload from get_forensic_page_payload() (recommended),
   including a normalized `forensicTranscript`.

This module provides:
- build_cida_pdf(report: dict) -> bytes
- make_report_payload_from_analysis(case_row, analysis_row, snapshot_row=None) -> dict
- upload_pdf_to_supabase(vector_id, analysis_version, pdf_bytes, bucket="forensic-reports") -> str

Notes
-----
- This file does NOT run SQL.
- Do not execute in Supabase SQL editor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

# ReportLab
from reportlab.lib import utils
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.colors import black, HexColor, lightgrey, whitesmoke


Json = Dict[str, Any]


# Optional: if you added services/forensic_normalize.py, we can use it without breaking imports.
# This keeps the module startup-safe even if the normalize module doesn't exist yet.
try:
    from services.forensic_normalize import normalize_forensic_transcript as _normalize_forensic_transcript  # type: ignore
except Exception:
    _normalize_forensic_transcript = None  # type: ignore


# -------------------------
# Public API
# -------------------------

def build_cida_pdf(report: Json, *, title: str = "CIDA Forensic Report") -> bytes:
    """
    Build a PDF from a report payload (dict) and return PDF bytes.

    The report dict can contain:
      - case_id / vector_id
      - source
      - article_url
      - headline_sq / headline_en or headline
      - audited_at / created_at
      - verdict / verdict_tier
      - verdict_summary_sq / verdict_summ
      - integrity_score / integrity_scor
      - blackmail_prob / blackmail_pr
      - key_tactics (list[str])
      - neutral_rewrite_sq / neutral_rewrite_en
      - forensicTranscript: normalized list[TranscriptBlock] OR
        segments: mixed list[str | dict] from the model
      - rebuttal_ledger: list[dict]

    Returns:
      PDF bytes suitable for upload/storage.
    """
    payload = normalize_report_payload(report)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="NOVARIC® Forensic Engine",
    )

    styles = _build_styles()

    story: List[Any] = []

    # Cover / header
    story.append(Paragraph(_escape(title), styles["h1"]))
    story.append(Spacer(1, 6))

    # Case meta
    meta_rows = [
        ("Case ID", payload.get("case_id") or payload.get("vector_id") or "—"),
        ("Source", payload.get("source") or "—"),
        ("Article URL", payload.get("article_url") or "—"),
        ("Audited At (UTC)", payload.get("audited_at") or "—"),
        ("Engine Version", payload.get("engine_version") or "—"),
        ("Analysis Version", str(payload.get("analysis_version") or "—")),
    ]
    story.append(_kv_table(meta_rows))
    story.append(Spacer(1, 10))

    # Headline(s)
    headline_sq = payload.get("headline_sq") or payload.get("headline") or ""
    headline_en = payload.get("headline_en") or ""
    if headline_sq or headline_en:
        story.append(Paragraph("Headline", styles["h2"]))
        if headline_sq:
            story.append(Paragraph(f"<b>SQ:</b> {_escape(headline_sq)}", styles["body"]))
        if headline_en:
            story.append(Paragraph(f"<b>EN:</b> {_escape(headline_en)}", styles["body"]))
        story.append(Spacer(1, 10))

    # Verdict + metrics summary
    story.append(Paragraph("Verdict & Metrics", styles["h2"]))
    verdict = payload.get("verdict") or payload.get("verdict_tier") or "—"
    integrity = payload.get("integrity_score")
    blackmail = payload.get("blackmail_prob")

    metric_rows = [
        ("Verdict", verdict),
        ("Integrity Score", _fmt_score(integrity)),
        ("Blackmail Probability", _fmt_score(blackmail)),
    ]
    story.append(_kv_table(metric_rows))
    story.append(Spacer(1, 10))

    # Key tactics
    tactics = payload.get("key_tactics") or []
    story.append(Paragraph("Key Tactics", styles["h2"]))
    if tactics:
        story.extend(_bullets(tactics, styles))
    else:
        story.append(Paragraph("—", styles["muted"]))
    story.append(Spacer(1, 10))

    # Verdict summaries
    story.append(Paragraph("Verdict Summary", styles["h2"]))
    vsq = payload.get("verdict_summary_sq") or payload.get("verdict_summ") or ""
    ven = payload.get("verdict_summary_en") or ""
    if vsq:
        story.append(Paragraph(f"<b>SQ:</b> {_escape(vsq)}", styles["body"]))
        story.append(Spacer(1, 4))
    if ven:
        story.append(Paragraph(f"<b>EN:</b> {_escape(ven)}", styles["body"]))
        story.append(Spacer(1, 4))
    if not vsq and not ven:
        story.append(Paragraph("—", styles["muted"]))
    story.append(Spacer(1, 10))

    # Neutral rewrite
    story.append(Paragraph("Neutral Rewrite", styles["h2"]))
    nr_sq = payload.get("neutral_rewrite_sq") or ""
    nr_en = payload.get("neutral_rewrite_en") or ""
    if nr_sq:
        story.append(Paragraph(f"<b>SQ:</b> {_escape(nr_sq)}", styles["body"]))
        story.append(Spacer(1, 4))
    if nr_en:
        story.append(Paragraph(f"<b>EN:</b> {_escape(nr_en)}", styles["body"]))
        story.append(Spacer(1, 4))
    if not nr_sq and not nr_en:
        story.append(Paragraph("—", styles["muted"]))
    story.append(Spacer(1, 12))

    # Redline transcript
    story.append(Paragraph("Redline Transcript", styles["h2"]))
    transcript = payload.get("forensicTranscript") or []
    if transcript:
        story.extend(_render_transcript(transcript, styles))
    else:
        story.append(Paragraph("—", styles["muted"]))
    story.append(Spacer(1, 12))

    # Rebuttal ledger
    story.append(Paragraph("Rebuttal Ledger", styles["h2"]))
    ledger = payload.get("rebuttal_ledger") or payload.get("rebuttalLedger") or []
    if ledger:
        story.append(_ledger_table(ledger, styles))
    else:
        story.append(Paragraph("—", styles["muted"]))

    # Footer hook with page numbers
    def _on_page(c, d):
        _draw_footer(c, d, payload)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    return buf.getvalue()


def make_report_payload_from_analysis(
    *,
    case_row: Json,
    analysis_row: Json,
    snapshot_row: Optional[Json] = None,
) -> Json:
    """
    Create a report payload from DB rows.

    Inputs are intended to be the Supabase row dicts from:
      - forensic_cases (case_row)
      - forensic_analyses (analysis_row)
      - forensic_snapshots (snapshot_row) optional

    Output is a unified payload usable by build_cida_pdf().
    """
    payload: Json = {}

    # Identity / meta
    payload["case_id"] = case_row.get("id")
    payload["vector_id"] = case_row.get("vector_id")
    payload["source"] = case_row.get("publisher") or case_row.get("source") or "—"
    payload["article_url"] = case_row.get("source_url") or case_row.get("article_url")

    payload["analysis_version"] = analysis_row.get("analysis_version")
    payload["engine_version"] = analysis_row.get("engine_version")
    payload["audited_at"] = _fmt_dt(analysis_row.get("created_at") or analysis_row.get("audited_at"))

    if snapshot_row:
        payload["snapshot_id"] = snapshot_row.get("id")
        payload["snapshot_seq"] = snapshot_row.get("snapshot_seq")

    # Analysis fields (depending on how you store)
    # Many setups store verdict/metrics inside JSONB columns.
    verdict_obj = analysis_row.get("verdict") or {}
    metrics_obj = analysis_row.get("metrics") or {}

    payload["verdict"] = verdict_obj.get("final") or analysis_row.get("verdict_tier") or analysis_row.get("verdict")
    payload["integrity_score"] = metrics_obj.get("integrity") or analysis_row.get("integrity_score") or analysis_row.get("integrity_scor")
    payload["blackmail_prob"] = metrics_obj.get("blackmail") or analysis_row.get("blackmail_prob") or analysis_row.get("blackmail_pr")

    payload["key_tactics"] = analysis_row.get("key_tactics") or []

    # Headline + summaries + rewrites if you store them; otherwise they may only exist in segments.
    payload["headline_sq"] = analysis_row.get("headline_sq")
    payload["headline_en"] = analysis_row.get("headline_en")
    payload["verdict_summary_sq"] = analysis_row.get("verdict_summary_sq")
    payload["verdict_summary_en"] = analysis_row.get("verdict_summary_en")
    payload["neutral_rewrite_sq"] = analysis_row.get("neutral_rewrite_sq")
    payload["neutral_rewrite_en"] = analysis_row.get("neutral_rewrite_en")

    # Transcript segments / ledger
    segments = analysis_row.get("forensic_segments") or analysis_row.get("segments") or []
    payload["segments"] = segments
    payload["rebuttal_ledger"] = analysis_row.get("rebuttal_ledger") or []

    # Normalize transcript for UI/PDF
    payload["forensicTranscript"] = normalize_transcript(segments)

    return payload


def upload_pdf_to_supabase(
    *,
    supabase_client: Any,
    vector_id: str,
    analysis_version: Union[int, str],
    pdf_bytes: bytes,
    bucket: str = "forensic-reports",
) -> str:
    """
    Upload PDF bytes to Supabase Storage and return the storage path.

    Parameters
    ----------
    supabase_client:
        The object returned by your db() helper, i.e. the Supabase python client.
    vector_id:
        e.g. "NOV_PMF_1"
    analysis_version:
        numeric or string, e.g. 1
    pdf_bytes:
        output of build_cida_pdf()
    bucket:
        storage bucket name

    Returns
    -------
    str: storage path (key) within bucket
    """
    safe_ver = str(analysis_version).strip() if analysis_version is not None else "na"
    path = f"entity_{vector_id}/analysis_v{safe_ver}/cida_report.pdf"

    # Supabase storage upload expects bytes-like for file content.
    # The python client API differs slightly by version; this should work with common supabase-py.
    res = supabase_client.storage.from_(bucket).upload(
        path=path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    # Some versions return dict-like; others return object. Best effort:
    if hasattr(res, "error") and res.error:
        raise RuntimeError(f"Supabase upload error: {res.error}")
    return path


# -------------------------
# Normalization helpers
# -------------------------

def normalize_report_payload(report: Json) -> Json:
    """
    Return a shallow-copied payload with standardized keys and normalized transcript.

    This makes build_cida_pdf() robust no matter which upstream payload format you pass in.
    """
    payload = dict(report or {})

    # unify url
    if "article_url" not in payload and "source_url" in payload:
        payload["article_url"] = payload.get("source_url")

    # unify verdict
    if "verdict" not in payload and "verdict_tier" in payload:
        payload["verdict"] = payload.get("verdict_tier")

    # unify metrics
    if "integrity_score" not in payload and "integrity_scor" in payload:
        payload["integrity_score"] = payload.get("integrity_scor")
    if "blackmail_prob" not in payload and "blackmail_pr" in payload:
        payload["blackmail_prob"] = payload.get("blackmail_pr")

    # unify summaries
    if "verdict_summary_sq" not in payload and "verdict_summ" in payload:
        payload["verdict_summary_sq"] = payload.get("verdict_summ")

    # audited_at formatting
    payload["audited_at"] = _fmt_dt(payload.get("audited_at") or payload.get("created_at"))

    # transcript: accept forensicTranscript already normalized, else derive from segments
    if not payload.get("forensicTranscript"):
        # Prefer the external normalizer if present (handles MVP + CIDA), otherwise fallback to local.
        if _normalize_forensic_transcript:
            payload["forensicTranscript"] = _normalize_forensic_transcript(payload)  # type: ignore
        else:
            payload["forensicTranscript"] = normalize_transcript(payload.get("segments") or [])

    # key tactics: ensure list
    kt = payload.get("key_tactics")
    if kt is None:
        payload["key_tactics"] = []
    elif isinstance(kt, str):
        payload["key_tactics"] = [kt]
    elif not isinstance(kt, list):
        payload["key_tactics"] = list(kt)

    return payload


def normalize_transcript(segments: Any) -> List[Json]:
    """
    Normalize mixed `segments` into a uniform list of transcript blocks.

    Output blocks:
      - { kind:"text", key:"...", text:"..." }
      - { kind:"redline", key:"...", id:"...", type:"malice|logic|void", text:"...", alert:"...", ... }

    This matches what your React UI should render, and what the PDF generator expects.
    """
    out: List[Json] = []
    if not segments:
        return out

    if not isinstance(segments, list):
        # Some DBs might store as JSON string; keep conservative.
        return out

    for i, seg in enumerate(segments):
        if isinstance(seg, str):
            t = seg.strip()
            if not t:
                continue
            out.append({"kind": "text", "key": f"t_{i}", "text": t})
        elif isinstance(seg, dict):
            rid = str(seg.get("id") or f"ev_{i}")
            rtype = str(seg.get("type") or "logic")
            text = (seg.get("text_sq") or seg.get("text") or "").strip()
            alert = (seg.get("alert_sq") or seg.get("alert") or "").strip()

            out.append(
                {
                    "kind": "redline",
                    "key": f"r_{rid}_{i}",
                    "id": rid,
                    "type": rtype if rtype in ("malice", "logic", "void") else "logic",
                    "text": text or "—",
                    "alert": alert or "—",
                    "category_sq": seg.get("category_sq"),
                    "category_en": seg.get("category_en"),
                    "description_sq": seg.get("description_sq"),
                    "description_en": seg.get("description_en"),
                }
            )
        else:
            # Unknown segment type; ignore safely
            continue

    return out


# -------------------------
# PDF rendering helpers
# -------------------------

def _build_styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    styles: Dict[str, ParagraphStyle] = {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=10.5,
            leading=14,
            textColor=HexColor("#666666"),
            spaceAfter=4,
        ),
        "redline_label": ParagraphStyle(
            "redline_label",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10.0,
            leading=13,
            textColor=HexColor("#111111"),
            spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            spaceAfter=2,
        ),
    }
    return styles


def _render_transcript(transcript: List[Json], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    flow: List[Any] = []
    for blk in transcript[:2000]:
        kind = blk.get("kind")
        if kind == "text":
            text = blk.get("text", "")
            if text.strip():
                flow.append(Paragraph(_escape(text), styles["body"]))
        elif kind == "redline":
            rtype = (blk.get("type") or "logic").upper()
            rid = blk.get("id") or "—"
            text = blk.get("text") or "—"
            alert = blk.get("alert") or "—"
            cat = blk.get("category_sq") or blk.get("category_en") or ""
            desc = blk.get("description_sq") or blk.get("description_en") or ""

            box = []
            box.append(Paragraph(f"[{_escape(rtype)}] Evidence ID: {_escape(str(rid))}", styles["redline_label"]))
            box.append(Paragraph(f"<b>Text:</b> {_escape(text)}", styles["small"]))
            box.append(Paragraph(f"<b>Alert:</b> {_escape(alert)}", styles["small"]))
            if cat:
                box.append(Paragraph(f"<b>Category:</b> {_escape(cat)}", styles["small"]))
            if desc:
                box.append(Paragraph(f"<b>Description:</b> {_escape(desc)}", styles["small"]))

            flow.append(_callout(box))
        else:
            # Unknown
            continue
    return flow


def _callout(paragraphs: List[Any]) -> Any:
    """
    Wrap paragraphs in a lightly styled table box to simulate a callout.

    ReportLab NOTE:
    - TableStyle does NOT support "INNERPADDING". Using it can raise:
      ValueError: Invalid style command 'INNERPADDING'
    - Use LEFTPADDING/RIGHTPADDING/TOPPADDING/BOTTOMPADDING instead.
    """
    t = Table([[p] for p in paragraphs], colWidths=[170 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#333333")),
                # ("INNERPADDING", (0, 0), (-1, -1), 6),  # invalid in ReportLab TableStyle
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, -1), whitesmoke),
            ]
        )
    )
    return KeepTogether([t, Spacer(1, 6)])


def _kv_table(rows: List[Tuple[str, str]]) -> Table:
    data = [[_escape(k), _escape(v)] for k, v in rows]
    tbl = Table(data, colWidths=[42 * mm, 128 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [whitesmoke, lightgrey]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.25, black),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def _ledger_table(ledger: List[Json], styles: Dict[str, ParagraphStyle]) -> Table:
    """
    Render rebuttal ledger as a table.
    """
    header = ["Claim (SQ)", "Type", "Evidence", "Risk"]
    rows = [header]
    for item in ledger[:200]:
        rows.append(
            [
                _escape(str(item.get("claim_sq") or item.get("claim_en") or "—")),
                _escape(str(item.get("type") or "—")),
                "Yes" if bool(item.get("hasEvidence")) else "No",
                _escape(str(item.get("risk") or "—")),
            ]
        )

    tbl = Table(rows, colWidths=[92 * mm, 28 * mm, 22 * mm, 22 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#DDDDDD")),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, black),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def _bullets(items: Iterable[str], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    out: List[Any] = []
    for s in list(items)[:60]:
        s2 = (s or "").strip()
        if not s2:
            continue
        out.append(Paragraph(f"• {_escape(s2)}", styles["body"]))
    return out


def _draw_footer(c, doc, payload: Json) -> None:
    """
    Draw page footer with case id and page number.
    """
    c.saveState()
    w, h = A4

    case_id = payload.get("case_id") or payload.get("vector_id") or "—"
    ts = payload.get("audited_at") or "—"

    footer_left = f"Case: {case_id}  |  Audited: {ts}"
    footer_right = f"Page {doc.page}"

    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#444444"))
    c.drawString(18 * mm, 10 * mm, footer_left[:120])
    c.drawRightString(w - 18 * mm, 10 * mm, footer_right)
    c.restoreState()


# -------------------------
# Formatting utilities
# -------------------------

def _fmt_score(v: Any) -> str:
    try:
        if v is None:
            return "—"
        if isinstance(v, str) and v.strip() == "":
            return "—"
        n = float(v)
        # Display integer if near-int
        if abs(n - round(n)) < 1e-6:
            return str(int(round(n)))
        return f"{n:.1f}"
    except Exception:
        return str(v) if v is not None else "—"


def _fmt_dt(v: Any) -> str:
    """
    Accepts ISO string, datetime, or None and returns an ISO-like UTC string.
    """
    if not v:
        return ""
    if isinstance(v, datetime):
        dt = v.astimezone(timezone.utc)
        return dt.replace(microsecond=0).isoformat()
    if isinstance(v, str):
        # Best-effort; don't hard-fail.
        return v
    return str(v)


def _escape(x: Any) -> str:
    """
    Escape text for ReportLab Paragraph (very small subset).
    """
    s = "" if x is None else str(x)
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )
