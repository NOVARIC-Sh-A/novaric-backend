# tests/test_api_core.py

def test_root_health(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "profiles_loaded" in data


def test_profiles_list(client):
    res = client.get("/api/profiles")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_news_endpoint(client):
    res = client.get("/api/v1/news")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_paragon_latest(client):
    res = client.get("/api/paragon/latest")
    assert res.status_code == 200
    assert "results" in res.json()


def test_paragon_recompute_mocked(client):
    """Recompute should work even with ALL scrapers mocked by pytest."""
    res = client.post("/api/paragon/recompute/1")
    assert res.status_code in (200, 404)  
    # 200 = metrics existed; 404 = no metrics → correct
