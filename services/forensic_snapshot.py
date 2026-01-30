import requests
from bs4 import BeautifulSoup
from utils.forensic_hash import sha256_text, normalize_text

def fetch_html(url: str) -> tuple[str, int, dict]:
    resp = requests.get(url, timeout=20, headers={"User-Agent": "NOVARIC-ForensicBot/1.0"})
    return resp.text, resp.status_code, dict(resp.headers)

def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove obvious noise
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ")
    return normalize_text(text)

def snapshot_payload(url: str) -> dict:
    html, status, headers = fetch_html(url)
    text = extract_main_text(html)
    content_hash = sha256_text(text)  # hash normalized extracted text (stable)
    return {
        "html": html,
        "plain_text": text,
        "http_status": status,
        "fetch_meta": {"headers": headers},
        "content_hash_sha256": content_hash,
    }
