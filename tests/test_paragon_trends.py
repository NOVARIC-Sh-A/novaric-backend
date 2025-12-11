def test_paragon_trends_latest(client):
    r = client.get("/api/paragon/trends/latest")
    assert r.status_code == 200
    assert "results" in r.json()
