# services/forensic_normalize.py
from typing import Any, Dict, List

Json = Dict[str, Any]


def normalize_transcript_from_cida(segments: Any) -> List[Json]:
    out: List[Json] = []
    if not isinstance(segments, list):
        return out

    for i, seg in enumerate(segments):
        if isinstance(seg, str):
            t = seg.strip()
            if t:
                out.append({"kind": "text", "key": f"cida_t_{i}", "text": t})
            continue

        if isinstance(seg, dict):
            rid = str(seg.get("id") or f"ev_{i}")
            rtype = (seg.get("type") or "logic").strip().lower()
            if rtype not in ("malice", "logic", "void"):
                rtype = "logic"

            out.append(
                {
                    "kind": "redline",
                    "key": f"cida_r_{rid}_{i}",
                    "id": rid,
                    "type": rtype,
                    "text": (seg.get("text_sq") or "").strip() or "—",
                    "alert": (seg.get("alert_sq") or "").strip() or "—",
                    "category_sq": seg.get("category_sq"),
                    "category_en": seg.get("category_en"),
                    "description_sq": seg.get("description_sq"),
                    "description_en": seg.get("description_en"),
                }
            )

    return out


def normalize_transcript_from_mvp(segments: Any, evidence_points: Any) -> List[Json]:
    out: List[Json] = []
    if not isinstance(segments, list):
        return out

    ev_map: Dict[str, Json] = {}
    if isinstance(evidence_points, list):
        for ev in evidence_points:
            if isinstance(ev, dict) and ev.get("id"):
                ev_map[str(ev["id"])] = ev

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            continue

        stype = seg.get("type")
        if stype == "text":
            t = (seg.get("value") or "").strip()
            if t:
                out.append({"kind": "text", "key": f"mvp_t_{i}", "text": t})

        elif stype == "evidence_ref":
            evid = str(seg.get("evidenceId") or f"ev_{i}")
            ev = ev_map.get(evid, {})

            rtype = (ev.get("type") or "malice").strip().lower()
            if rtype not in ("malice", "logic", "void"):
                rtype = "malice"

            out.append(
                {
                    "kind": "redline",
                    "key": f"mvp_r_{evid}_{i}",
                    "id": evid,
                    "type": rtype,
                    "text": (seg.get("value") or ev.get("text") or "").strip() or "—",
                    "alert": (ev.get("alert") or "NEUTRALITY ALERT").strip(),
                    "category_sq": ev.get("category") or "Loaded Labeling",
                    "description_sq": ev.get("description")
                    or "Potentially prejudicial language detected.",
                }
            )

    return out


def normalize_forensic_transcript(payload: Json) -> List[Json]:
    segments = payload.get("segments")

    # MVP format detection
    if (
        isinstance(segments, list)
        and segments
        and isinstance(segments[0], dict)
        and "value" in segments[0]
    ):
        return normalize_transcript_from_mvp(
            segments, payload.get("evidence_points") or []
        )

    # Default to GPT CIDA format
    return normalize_transcript_from_cida(segments or [])
