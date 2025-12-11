"""
politician_loader.py (Compatibility Wrapper)

This module exists ONLY to preserve backward compatibility
for older modules that still import:

    from politician_loader import load_metrics_for

All real metric loading logic now lives in:

    etl/metric_loader.py

Do NOT add logic here — keep all evidence assembly centralized.
"""

from typing import Dict, Any
from etl.metric_loader import load_metrics_for as _load_metrics_for


def load_metrics_for(politician_id: int) -> Dict[str, Any]:
    """
    Thin wrapper that forwards calls to the unified PARAGON metric loader.

    New core loader:
        etl.metric_loader.load_metrics_for()
    """
    return _load_metrics_for(politician_id)
