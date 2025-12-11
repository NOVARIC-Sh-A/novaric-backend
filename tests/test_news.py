def test_news_endpoint(client):
    r = client.get("/api/v1/news")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
