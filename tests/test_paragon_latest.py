def test_paragon_latest(client):
    r = client.get("/api/paragon/latest")
    assert r.status_code == 200
    assert "results" in r.json()


def test_paragon_latest_single(client):
    r = client.get("/api/paragon/latest/1")
    # Supabase mocked → returns 404
    assert r.status_code in (200, 404)
