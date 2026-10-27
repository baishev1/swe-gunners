from fastapi.testclient import TestClient


def test_create_venue(client: TestClient, organizer_headers: dict[str, str]) -> None:
    res = client.post(
        "/api/v1/venues",
        json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"},
        headers=organizer_headers,
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Astana Hub Almaty"
    assert "id" in res.json()


def test_list_venues(client: TestClient, organizer_headers: dict[str, str]) -> None:
    client.post(
        "/api/v1/venues",
        json={"name": "Kazakhconcert", "address": "Abylai Khan 83"},
        headers=organizer_headers,
    )

    res = client.get("/api/v1/venues")
    assert res.status_code == 200
    names = [v["name"] for v in res.json()]
    assert "Kazakhconcert" in names


def test_create_venue_requires_token(client: TestClient) -> None:
    res = client.post("/api/v1/venues", json={"name": "Hall", "address": "Abay 1"})
    assert res.status_code == 401


def test_attendee_cannot_create_venue(client: TestClient, attendee_headers: dict[str, str]) -> None:
    res = client.post(
        "/api/v1/venues",
        json={"name": "Hall", "address": "Abay 1"},
        headers=attendee_headers,
    )
    assert res.status_code == 403
