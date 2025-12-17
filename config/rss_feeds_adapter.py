"""
rss_feeds_adapter.py

Drop-in adapter that transparently upgrades existing feed access
to weighted, trust-aware ordering WITHOUT requiring code changes
at call sites.

Usage:
- Import this module once at application startup
- Or alias it as rss_feeds in sys.modules
"""

import sys
import rss_feeds as _rss


# --------------------------------------------------------------
# Internal wrappers (do NOT expose new API surface)
# --------------------------------------------------------------

def _weighted_profile_feeds(profile_type: str):
    """
    Adapter replacement for get_feeds_for_profile_type
    """
    feeds = _rss.get_feeds_for_profile_type(profile_type)
    return _rss.rank_feeds(feeds)


def _weighted_news_category_feeds(category: str):
    """
    Adapter replacement for get_feeds_for_news_category
    """
    feeds = _rss.get_feeds_for_news_category(category)
    return _rss.rank_feeds(feeds)


# --------------------------------------------------------------
# Monkey-patch original module functions
# --------------------------------------------------------------

_rss.get_feeds_for_profile_type = _weighted_profile_feeds
_rss.get_feeds_for_news_category = _weighted_news_category_feeds


# --------------------------------------------------------------
# Optional: re-export module under original name (hard override)
# --------------------------------------------------------------

sys.modules["rss_feeds"] = _rss
