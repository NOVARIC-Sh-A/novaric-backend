# services/ner_config.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# Base weights must sum to 1.0 across the four base dimensions.
# If you prefer integers summing to 100, your engine already divides by 100.0, so keep ints.
NER_WEIGHTS: Dict[str, int] = {
    "SRS": 30,
    "CIS": 25,
    "CSC": 20,
    "TRF": 25,
}

def validate_weights() -> None:
    total = int(NER_WEIGHTS["SRS"] + NER_WEIGHTS["CIS"] + NER_WEIGHTS["CSC"] + NER_WEIGHTS["TRF"])
    if total != 100:
        raise ValueError(f"NER_WEIGHTS must sum to 100. Current sum = {total}")

validate_weights()

@dataclass(frozen=True)
class NerBreakdown:
    SRS: int
    CIS: int
    CSC: int
    TRF: int
    ECM: float

@dataclass(frozen=True)
class NerResult:
    ecosystemRating: int
    breakdown: NerBreakdown
    nerVersion: str = "ner_v1.0"
