# tests/conftest.py

from readline import backend
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import AFTER mocks are defined
import main  


@pytest.fixture(scope="session")
def client():
    return TestClient(main.app)


# ----------------------------------------------------------
# Disable RSS network calls
# ----------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_feedparser():
    with patch("feedparser.parse") as mock:
        mock.return_value = type("Feed", (), {
            "entries": [],
            "bozo": False,
            "status": 200
        })
        yield


# ----------------------------------------------------------
# Disable Supabase for ALL tests
# ----------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_supabase():
    with patch("utils.supabase_client._get") as mock:
        mock.return_value = []
        yield


# ----------------------------------------------------------
# Disable Gemini (media & social scrapers)
# ----------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_gemini():
    with patch("google.generativeai.GenerativeModel") as mock_model:
        instance = mock_model.return_value
        instance.generate_content.return_value = type("Obj", (), {"text": '{"influence_boost": 0}'})
        yield
