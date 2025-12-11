def test_get_profiles(client):
    r = client.get("/api/profiles")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_profile_not_found(client):
    r = client.get("/api/profiles/999999")
    assert r.status_code == 404
