def test_momentum(client):
    r = client.get("/api/paragon/trends/momentum/1")
    assert r.status_code in (200, 404)
