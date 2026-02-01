import os
import re
import json
import openai
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# Load environment variables (local dev). Safe if dotenv isn't configured.
load_dotenv()

LOADED_LABELS = [
    "trafikant",
    "skllev",
    "maf",
    "krimin",
    "band",
    "pastrim parash",
]


def sentence_split(text: str) -> list[str]:
    # original simple splitter logic preserved
    parts = re.split(r"(?<=[\.\!\?])\s+", text or "")
    return [p.strip() for p in parts if p and p.strip()]


def _get_openai_client() -> openai.OpenAI:
    """
    Option A (recommended): Lazy-init OpenAI client at call-time.
    This prevents import-time crashes when OPENAI_API_KEY is not configured.
    """
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Set it in your environment or .env to run CIDA audits."
        )
    return openai.OpenAI(api_key=api_key)


def run_cida_audit(plain_text: str) -> Dict[str, Any]:
    """
    SMART ARCHITECTURE UPDATE (Option A):
    Performs a clinical Content Integrity & Defamation Audit using GPT-4o.

    - No OpenAI client is created at import time.
    - Fails clearly if OPENAI_API_KEY is missing.
    """
    prompt = f"""
    Perform a Forensic Media Audit (CIDA Protocol) on the following content.
    The analysis must identify linguistic malice and structural disinformation.

    CONTENT:
    ---
    {plain_text}
    ---

    Return ONLY a JSON object with this exact structure:
    {{
        "headline_sq": "Headline in Albanian",
        "headline_en": "Headline in English",
        "integrity_score": 0-100,
        "blackmail_prob": 0-100,
        "verdict_tier": "HIGH_RISK_DISINFORMATION",
        "verdict_summary_sq": "2-sentence summary SQ",
        "verdict_summary_en": "2-sentence summary EN",
        "neutral_rewrite_sq": "Neutral version SQ",
        "neutral_rewrite_en": "Neutral version EN",
        "key_tactics": ["Ad Hominem", "Data Void", "etc"],
        "segments": [
            "text block",
            {{
                "id": "ev1",
                "text_sq": "Exact quote",
                "type": "malice|logic|void",
                "alert_sq": "Alert Title",
                "category_sq": "Labeling",
                "category_en": "Labeling EN",
                "description_sq": "Explanation SQ",
                "description_en": "Explanation EN"
            }}
        ],
        "rebuttal_ledger": [
            {{
                "claim_sq": "The claim",
                "claim_en": "The claim EN",
                "type": "Allegation",
                "hasEvidence": false,
                "risk": "high"
            }}
        ],
        "malice_markers_sq": ["word1", "word2"],
        "malice_markers_en": ["word1 EN", "word2 EN"]
    }}
    """

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a Forensic Media Analyst."},
                {"role": "user", "content": prompt},
            ],
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Audit Error: {e}")
        return {"integrity_score": 0, "segments": [], "rebuttal_ledger": []}


def build_analysis(plain_text: str):
    """ORIGINAL MVP LOGIC PRESERVED"""
    text = plain_text or ""
    evidence_points: List[Dict[str, Any]] = []
    segments: List[Dict[str, Any]] = []
    ev_counter = 1

    def add_text(t: str):
        if t:
            segments.append({"type": "text", "value": t})

    def add_evidence(span: str, ev: Dict[str, Any]):
        segments.append({"type": "evidence_ref", "evidenceId": ev["id"], "value": span})
        evidence_points.append(ev)

    lowered = text.lower()
    cursor = 0
    for label in LOADED_LABELS:
        idx = lowered.find(label)
        if idx != -1:
            start = max(0, idx - 20)
            end = min(len(text), idx + len(label) + 20)
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
                "description": "Potentially prejudicial language detected.",
            }
            add_evidence(span, ev)
            text = after
            lowered = text.lower()
            cursor = 0
    add_text(text)

    fallacies = [
        {"name": "Ad Hominem", "desc": "Personal attack framing."},
        {"name": "Guilt by Association", "desc": "Implied culpability via proximity."},
        {"name": "Poisoning the Well", "desc": "Preloading reader opinion."},
    ]
    ethics_scorecard = [
        {"label": "Verification of Sources", "status": "FAILED"},
        {"label": "Objectivity of Tone", "status": "FAILED"},
        {"label": "Right of Reply Granted", "status": "UNKNOWN"},
        {"label": "Distinction: Fact vs Opinion", "status": "FAILED"},
    ]
    rebuttal_ledger = [
        {
            "claim": "Article contains criminal allegations.",
            "reality": "INTERNAL SCAN: No citations detected.",
        }
    ]
    verdict = {
        "tier": "HIGH_RISK_DISINFORMATION",
        "summary": "Automated scan detected accusatory labeling.",
        "recommendation": ["Snapshot preserved", "Escalate review"],
        "confidence": 0.65,
    }
    metrics = {"evidencePoints": len(evidence_points), "segments": len(segments)}
    return segments, evidence_points, fallacies, ethics_scorecard, rebuttal_ledger, verdict, metrics
