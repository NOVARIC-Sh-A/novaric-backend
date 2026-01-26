# etl/evidence/contracts.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class EvidenceItem:
    source_key: str
    url: str
    title: str = ""
    published_at: Optional[str] = None  # ISO string
    content_type: str = "article"
    language: str = "sq"
    snippet: str = ""
    raw_text: str = ""

    entities: Dict[str, Any] = field(default_factory=dict)
    topics: Any = field(default_factory=list)  # list
    signals: Dict[str, Any] = field(default_factory=dict)
    extraction_confidence: float = 0.6

    politician_id: Optional[int] = None
