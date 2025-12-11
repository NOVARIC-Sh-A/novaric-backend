import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app

@pytest.fixture
def client():
    return TestClient(app)


# Disable RSS parsing during tests
@pytest.fixture(autouse=True)
def mock_feedparser():
    with patch("feedparser.parse") as mock:
        mock.return_value = type("Feed", (), {"entries": [], "bozo": False, "status": 200})
        yield


# Disable Supabase networking
@pytest.fixture(autouse=True)
def mock_supabase():
    with patch("utils.supabase_client._get") as get_mock:
        get_mock.return_value = []
        yield