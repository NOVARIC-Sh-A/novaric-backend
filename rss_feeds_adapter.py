"""
rss_feeds_adapter.py

Drop-in adapter that transparently upgrades existing feed access
to weighted, trust-aware ordering WITHOUT requiring code changes
at call sites.

Usage:
- Import this module once at application startup (e.g. in main.py)
- Must be imported BEFORE config.rss_feeds is imported anywhere else
"""

import sys
from config import rss_feeds as _rss


# --------------------------------------------------------------
# Internal wrappers (do NOT expose new API surface)
# --------------------------------------------------------------

def _weighted_profile_feeds(profile_type: str):
    """
    Adapter replacement for get_feeds_for_profile_type.
    Preserves original signature and behavior, but applies
    deterministic ranking using trust + tier metadata.
    """
    feeds = _rss.get_feeds_for_profile_type(profile_type)
    return _rss.rank_feeds(feeds)


def _weighted_news_category_feeds(category: str):
    """
    Adapter replacement for get_feeds_for_news_category.
    Preserves backward compatibility while ensuring
    quality-ranked feed ordering.
    """
    feeds = _rss.get_feeds_for_news_category(category)
    return _rss.rank_feeds(feeds)


# --------------------------------------------------------------
# Monkey-patch original module functions (in-place)
# --------------------------------------------------------------

_rss.get_feeds_for_profile_type = _weighted_profile_feeds
_rss.get_feeds_for_news_category = _weighted_news_category_feeds


# --------------------------------------------------------------
# Ensure all future imports see the patched module
# --------------------------------------------------------------

sys.modules["config.rss_feeds"] = _rss
