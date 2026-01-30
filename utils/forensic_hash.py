import hashlib

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def normalize_text(s: str) -> str:
    # stable normalization for hashing (keep it deterministic)
    return " ".join(s.replace("\r", "\n").split())
