# etl/evidence/hash_utils.py
from __future__ import annotations
import hashlib
from urllib.parse import urlparse, urlunparse

def canonicalize_url(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    p = urlparse(u)
    # remove fragments, normalize scheme/host, keep path+query
    netloc = p.netloc.lower().replace("www.", "")
    scheme = (p.scheme or "https").lower()
    return urlunparse((scheme, netloc, p.path or "/", "", p.query or "", ""))

def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def url_hash(url: str) -> str:
    return sha256_text(canonicalize_url(url))
