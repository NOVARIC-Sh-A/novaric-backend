def test_root_endpoint(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()

def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}
