# etl/sources/source_registry.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class SourceDef:
    key: str
    name: str
    base_url: str
    trust_tier: int = 2
    scrape_method: str = "html"  # html|rss|api|pdf
    enabled: bool = True
    refresh_minutes: int = 1440
    notes: str = ""

def get_sources() -> List[SourceDef]:
    # Start minimal; expand gradually.
    return [
        SourceDef(
            key="rss_albanian_media",
            name="Albanian Media RSS (configured)",
            base_url="(multiple feeds in config/rss_feeds.py)",
            trust_tier=2,
            scrape_method="rss",
            notes="Uses existing feed registry in config/rss_feeds.py",
        ),
    ]
