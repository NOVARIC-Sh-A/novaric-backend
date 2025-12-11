import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# ----------------------------------------------------------------------
# FIX: Ensure project root is on PYTHONPATH
# ----------------------------------------------------------------------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from main import app  # now import works


@pytest.fixture
def client():
    return TestClient(app)


# ----------------------------------------------------------------------
# Disable RSS parsing during tests
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_feedparser():
    with patch("feedparser.parse") as mock:
        mock.return_value = type(
            "Feed",
            (),
            {"entries": [], "bozo": False, "status": 200}
        )
        yield


# ----------------------------------------------------------------------
# Disable Supabase networking
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_supabase():
    with patch("utils.supabase_client._get") as get_mock:
        get_mock.return_value = []
        yield
