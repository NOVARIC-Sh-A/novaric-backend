# services/ner_engine.py
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Iterable, List, Tuple

from config.rss_feeds import get_feed_meta
from services.ner_config import NER_WEIGHTS, NerBreakdown, NerResult

_CLICKBAIT_PATTERNS = [
    r"\bshocking\b",
    r"\byou won[’']?t believe\b",
    r"\bwhat happened next\b",
    r"\bexclusive\b",
    r"\bbreaking\b",
    r"\bmust see\b",
    r"\bunbelievable\b",
]

def _clamp_int(x: float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(x))))

def _safe_parse_datetime(ts: str) -> datetime | None:
    if not ts:
        return None
    # feedparser often returns RFC822; your API stores strings. We'll try ISO first, then fallback.
    try:
        # Handles "2025-12-18T12:34:56+00:00"
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None

# ---------------------------
# SRS — Source Reliability
# ---------------------------
def compute_srs(feed_url: str) -> int:
    meta = get_feed_meta(feed_url)
    # Base trust score with small tier adjustment
    tier_bonus = {1: 8, 2: 3, 3: -5}.get(meta.tier, 0)
    return _clamp_int(meta.trust_score + tier_bonus)

# ---------------------------
# CIS — Content Integrity
# Deterministic heuristics (no LLM)
# ---------------------------
def compute_cis(title: str, summary: str) -> int:
    text = (title or "").strip() + " " + (summary or "").strip()
    text = text.strip()

    if not text:
        return 30

    score = 70.0

    # Length sanity
    n = len(text)
    if n < 80:
        score -= 20
    elif n < 160:
        score -= 10
    elif n > 2500:
        score -= 5  # very long summaries sometimes contain noise

    # Excessive punctuation / shouting
    exclam = text.count("!")
    if exclam >= 3:
        score -= min(15, exclam * 3)

    # ALL CAPS ratio penalty
    letters = [c for c in text if c.isalpha()]
    if letters:
        caps = sum(1 for c in letters if c.isupper())
        caps_ratio = caps / max(1, len(letters))
        if caps_ratio > 0.35:
            score -= 12

    # Clickbait pattern penalty
    lower = text.lower()
    for pat in _CLICKBAIT_PATTERNS:
        if re.search(pat, lower):
            score -= 8

    # Too many repeated tokens (simple spam signal)
    tokens = re.findall(r"[a-zA-ZÀ-ž0-9']+", lower)
    if tokens:
        unique = len(set(tokens))
        diversity = unique / max(1, len(tokens))
        if diversity < 0.35:
            score -= 10

    return _clamp_int(score)

# ---------------------------
# TRF — Temporal Relevance
# Deterministic decay by age
# ---------------------------
def compute_trf(published_ts: str, now_utc: datetime) -> int:
    dt = _safe_parse_datetime(published_ts)
    if dt is None:
        return 55  # unknown timestamp → conservative

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    age_hours = (now_utc - dt).total_seconds() / 3600.0
    if age_hours < 0:
        age_hours = 0

    if age_hours <= 6:
        return 100
    if age_hours <= 24:
        return 80
    if age_hours <= 72:
        return 60
    if age_hours <= 168:
        return 40
    return 20

# ---------------------------
# CSC — Cross-Source Corroboration
# Deterministic clustering by title token overlap
# ---------------------------
def _fingerprint_title(title: str) -> set[str]:
    t = (title or "").lower()
    tokens = re.findall(r"[a-zA-ZÀ-ž0-9']+", t)
    stop = {"the", "and", "or", "of", "to", "in", "a", "an", "for", "on", "with", "nga", "dhe", "ose", "ne", "per"}
    core = [x for x in tokens if len(x) >= 4 and x not in stop]
    return set(core[:20])  # cap for stability

def compute_csc(current_title: str, peer_titles: Iterable[str]) -> int:
    fp = _fingerprint_title(current_title)
    if not fp:
        return 45

    corroborators = 0
    for pt in peer_titles:
        pf = _fingerprint_title(pt)
        if not pf:
            continue
        inter = len(fp.intersection(pf))
        union = len(fp.union(pf))
        jacc = inter / max(1, union)
        if jacc >= 0.35:
            corroborators += 1

    # Score mapping: more corroboration → higher, capped.
    if corroborators <= 0:
        return 45
    if corroborators == 1:
        return 65
    if corroborators == 2:
        return 78
    if corroborators == 3:
        return 86
    return 92

# ---------------------------
# ECM — Ecosystem Context Multiplier
# Deterministic, low-impact modifier
# ---------------------------
def compute_ecm(source_type: str) -> float:
    # Keep ECM within 0.90..1.15 range.
    # Albania gets a small boost for local relevance; Balkan moderate; International neutral.
    if source_type == "albanian":
        return 1.08
    if source_type == "balkan":
        return 1.04
    return 1.00

# ---------------------------
# NER — Final aggregation
# ---------------------------
def compute_ner(
    *,
    feed_url: str,
    source_type: str,
    title: str,
    summary: str,
    published_ts: str,
    peer_titles: List[str],
    now_utc: datetime | None = None,
) -> NerResult:
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    srs = compute_srs(feed_url)
    cis = compute_cis(title, summary)
    csc = compute_csc(title, peer_titles)
    trf = compute_trf(published_ts, now_utc)
    ecm = compute_ecm(source_type)

    base = (
        srs * (NER_WEIGHTS["SRS"] / 100.0)
        + cis * (NER_WEIGHTS["CIS"] / 100.0)
        + csc * (NER_WEIGHTS["CSC"] / 100.0)
        + trf * (NER_WEIGHTS["TRF"] / 100.0)
    )

    final = _clamp_int(base * ecm)

    return NerResult(
        ecosystemRating=final,
        breakdown=NerBreakdown(SRS=srs, CIS=cis, CSC=csc, TRF=trf, ECM=float(ecm)),
    )
