"""
rss_feeds_adapter.py

Drop-in adapter that transparently upgrades existing feed access
to weighted, trust-aware ordering WITHOUT requiring code changes
at call sites.

Usage:
- Import this module once at application startup (e.g. in main.py)
- Must be imported BEFORE config.rss_feeds is imported anywhere else
"""

from __future__ import annotations

import sys
import logging
from typing import List

from config import rss_feeds as _rss

logger = logging.getLogger("novaric-backend")


# ==============================================================
# Preserve ORIGINAL functions (CRITICAL to avoid recursion)
# ==============================================================

_ORIGINAL_GET_FEEDS_FOR_PROFILE_TYPE = _rss.get_feeds_for_profile_type
_ORIGINAL_GET_FEEDS_FOR_NEWS_CATEGORY = _rss.get_feeds_for_news_category


# ==============================================================
# Internal wrappers (DO NOT expose new API surface)
# ==============================================================

def _weighted_profile_feeds(profile_type: str) -> List[str]:
    """
    Adapter replacement for get_feeds_for_profile_type.

    Behavior:
    - Calls the ORIGINAL function (not patched)
    - Applies deterministic ranking using trust + tier metadata
    """
    try:
        feeds = _ORIGINAL_GET_FEEDS_FOR_PROFILE_TYPE(profile_type)
    except Exception as e:
        logger.error(f"Error resolving profile feeds for '{profile_type}': {e}")
        return []

    try:
        return _rss.rank_feeds(feeds)
    except Exception as e:
        logger.warning(f"Feed ranking failed (profile_type={profile_type}): {e}")
        return feeds


def _weighted_news_category_feeds(category: str) -> List[str]:
    """
    Adapter replacement for get_feeds_for_news_category.

    Guarantees:
    - Backward compatibility
    - NO recursion
    - Deterministic, quality-ranked ordering
    """
    try:
        feeds = _ORIGINAL_GET_FEEDS_FOR_NEWS_CATEGORY(category)
    except Exception as e:
        logger.error(f"Error resolving news feeds for category '{category}': {e}")
        return []

    try:
        return _rss.rank_feeds(feeds)
    except Exception as e:
        logger.warning(f"Feed ranking failed (category={category}): {e}")
        return feeds


# ==============================================================
# Monkey-patch original module functions (SAFE + IDEMPOTENT)
# ==============================================================

def _apply_patches() -> None:
    """
    Apply monkey patches exactly once.
    Safe to call multiple times.
    """
    if _rss.get_feeds_for_profile_type is not _weighted_profile_feeds:
        _rss.get_feeds_for_profile_type = _weighted_profile_feeds

    if _rss.get_feeds_for_news_category is not _weighted_news_category_feeds:
        _rss.get_feeds_for_news_category = _weighted_news_category_feeds


_apply_patches()


# ==============================================================
# Ensure all future imports see the patched module
# ==============================================================

sys.modules["config.rss_feeds"] = _rss
