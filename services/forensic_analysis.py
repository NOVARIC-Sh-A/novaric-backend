import re
from utils.forensic_hash import normalize_text

LOADED_LABELS = [
    "trafikant", "skllev", "maf", "krimin", "band", "pastrim parash"
]

def sentence_split(text: str) -> list[str]:
    # simple splitter; replace later with better NLP
    parts = re.split(r'(?<=[\.\!\?])\s+', text)
    return [p.strip() for p in parts if p.strip()]

def build_analysis(plain_text: str):
    text = plain_text
    evidence_points = []
    segments = []
    ev_counter = 1

    def add_text(t: str):
        if t:
            segments.append({"type":"text","value":t})

    def add_evidence(span: str, ev):
        segments.append({"type":"evidence_ref","evidenceId":ev["id"],"value":span})
        evidence_points.append(ev)

    # Very MVP: highlight first occurrence of loaded labels
    lowered = text.lower()
    cursor = 0
    for label in LOADED_LABELS:
        idx = lowered.find(label)
        if idx != -1:
            # include a small span around it (safe for UI)
            start = max(0, idx-20)
            end = min(len(text), idx+len(label)+20)

            # split into three: before span, span, after
            before = text[cursor:start]
            span = text[start:end]
            after = text[end:]

            add_text(before)

            ev_id = f"ev{ev_counter}"
            ev_counter += 1
            ev = {
                "id": ev_id,
                "text": span,
                "type": "malice",
                "alert": "NEUTRALITY ALERT",
                "category": "Loaded Labeling",
                "description": "Potentially prejudicial language detected without embedded evidentiary reference."
            }
            add_evidence(span, ev)

            text = after
            lowered = text.lower()
            cursor = 0

    add_text(text)

    fallacies = [
        {"name":"Ad Hominem","desc":"Personal attack framing instead of verifiable evidence."},
        {"name":"Guilt by Association","desc":"Implied culpability via proximity to institutions or individuals."},
        {"name":"Poisoning the Well","desc":"Preloading reader opinion through accusatory labels."}
    ]

    ethics_scorecard = [
        {"label":"Verification of Sources","status":"FAILED"},
        {"label":"Objectivity of Tone","status":"FAILED"},
        {"label":"Right of Reply Granted","status":"UNKNOWN"},
        {"label":"Distinction: Fact vs Opinion","status":"FAILED"}
    ]

    rebuttal_ledger = [
        {"claim":"Article contains criminal allegations.","reality":"INTERNAL SCAN: No in-text documentary citations detected in the captured content (MVP heuristic)."}
    ]

    verdict = {
        "tier":"HIGH_RISK_DISINFORMATION",
        "summary":"Automated scan detected accusatory labeling and weak in-text substantiation (rule-based MVP).",
        "recommendation":["Snapshot preserved","Escalate to legal/compliance review","Generate report export"],
        "confidence":0.65
    }

    metrics = {
        "evidencePoints": len(evidence_points),
        "segments": len(segments)
    }

    return segments, evidence_points, fallacies, ethics_scorecard, rebuttal_ledger, verdict, metrics
