from fastapi.testclient import TestClient


def test_create_venue(client: TestClient) -> None:
    res = client.post(
        "/api/v1/venues", json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"}
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Astana Hub Almaty"
    assert "id" in res.json()


def test_list_venues(client: TestClient) -> None:
    client.post("/api/v1/venues", json={"name": "Kazakhconcert", "address": "Abylai Khan 83"})

    res = client.get("/api/v1/venues")
    assert res.status_code == 200
    names = [v["name"] for v in res.json()]
    assert "Kazakhconcert" in names
