from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def create_venue(client: TestClient, headers: dict[str, str]) -> str:
    res = client.post(
        "/api/v1/venues",
        json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"},
        headers=headers,
    )
    return res.json()["id"]


def sample_event_payload(venue_id: str) -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Almaty Tech Meetup",
        "description": "Tech discussions and networking in Almaty",
        "category": "Technology",
        "venue_id": venue_id,
        "start_time": (now + timedelta(days=5)).isoformat(),
        "end_time": (now + timedelta(days=5, hours=3)).isoformat(),
        "timezone": "Asia/Almaty",
        "capacity": 150,
        "visibility": "public",
        "is_assigned_seating": False,
    }


def test_create_event(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    response = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "draft"
    assert data["capacity"] == 150
    assert "id" in data


def test_get_event_detail(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    create_res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    event_id = create_res.json()["id"]

    res = client.get(f"/api/v1/events/detail?event_id={event_id}")
    assert res.status_code == 200
    assert res.json()["id"] == event_id


def test_get_event_detail_not_found(client: TestClient, organizer_headers: dict[str, str]) -> None:
    fake_id = uuid4()
    res = client.get(f"/api/v1/events/detail?event_id={fake_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Event not found"


def test_update_event(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    create_res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    event_id = create_res.json()["id"]

    update_payload = {"title": "Updated Title", "capacity": 200}
    res = client.patch(
        f"/api/v1/events/update?event_id={event_id}", json=update_payload, headers=organizer_headers
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"
    assert res.json()["capacity"] == 200


def test_publish_and_unpublish_event(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    create_res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    event_id = create_res.json()["id"]

    pub_res = client.post(f"/api/v1/events/publish?event_id={event_id}", headers=organizer_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    unpub_res = client.post(
        f"/api/v1/events/unpublish?event_id={event_id}", headers=organizer_headers
    )
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == "unpublished"


def test_cancel_event_and_guard(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    create_res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    event_id = create_res.json()["id"]

    cancel_res = client.post(
        f"/api/v1/events/cancel?event_id={event_id}", headers=organizer_headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    bad_update = client.patch(
        f"/api/v1/events/update?event_id={event_id}",
        json={"title": "Should Fail"},
        headers=organizer_headers,
    )
    assert bad_update.status_code == 400
    assert bad_update.json()["detail"] == "Cannot modify a cancelled event"


def test_duplicate_event(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    create_res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    event_id = create_res.json()["id"]

    res = client.post(f"/api/v1/events/duplicate?event_id={event_id}", headers=organizer_headers)
    assert res.status_code == 201
    dup_data = res.json()
    assert dup_data["id"] != event_id
    assert dup_data["title"] == f"{payload['title']} (Copy)"
    assert dup_data["status"] == "draft"


def test_list_events(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload1 = sample_event_payload(create_venue(client, organizer_headers))
    client.post("/api/v1/events", json=payload1, headers=organizer_headers)

    payload2 = sample_event_payload(create_venue(client, organizer_headers))
    payload2["title"] = "Published Concert"
    res2 = client.post("/api/v1/events", json=payload2, headers=organizer_headers)
    id2 = res2.json()["id"]
    client.post(f"/api/v1/events/publish?event_id={id2}", headers=organizer_headers)

    list_res = client.get("/api/v1/events")
    assert list_res.status_code == 200
    titles = [e["title"] for e in list_res.json()]
    assert "Published Concert" in titles


def test_create_event_unknown_venue(client: TestClient, organizer_headers: dict[str, str]) -> None:
    res = client.post(
        "/api/v1/events", json=sample_event_payload(str(uuid4())), headers=organizer_headers
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Venue not found"


def test_create_event_sets_current_organizer(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    me = client.get("/api/v1/auth/me", headers=organizer_headers)
    payload = sample_event_payload(create_venue(client, organizer_headers))
    res = client.post("/api/v1/events", json=payload, headers=organizer_headers)
    assert res.json()["organizer_id"] == me.json()["id"]


def test_create_event_requires_token(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    assert client.post("/api/v1/events", json=payload).status_code == 401


def test_attendee_cannot_create_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    res = client.post("/api/v1/events", json=payload, headers=attendee_headers)
    assert res.status_code == 403


def test_other_organizer_cannot_modify_event(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    event_id = client.post("/api/v1/events", json=payload, headers=organizer_headers).json()["id"]

    update_res = client.patch(
        f"/api/v1/events/update?event_id={event_id}",
        json={"title": "Hijacked"},
        headers=other_organizer_headers,
    )
    assert update_res.status_code == 404

    publish_res = client.post(
        f"/api/v1/events/publish?event_id={event_id}", headers=other_organizer_headers
    )
    assert publish_res.status_code == 404

    duplicate_res = client.post(
        f"/api/v1/events/duplicate?event_id={event_id}", headers=other_organizer_headers
    )
    assert duplicate_res.status_code == 404


def test_public_list_hides_drafts(client: TestClient, organizer_headers: dict[str, str]) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    client.post("/api/v1/events", json=payload, headers=organizer_headers)

    res = client.get("/api/v1/events")
    assert res.status_code == 200
    assert res.json() == []


def test_my_events_shows_only_own(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
) -> None:
    payload = sample_event_payload(create_venue(client, organizer_headers))
    client.post("/api/v1/events", json=payload, headers=organizer_headers)
    payload["title"] = "Other Draft"
    client.post("/api/v1/events", json=payload, headers=other_organizer_headers)

    mine = client.get("/api/v1/events/mine", headers=organizer_headers)
    assert [e["title"] for e in mine.json()] == ["Almaty Tech Meetup"]

    published = client.get("/api/v1/events/mine?status=published", headers=organizer_headers)
    assert published.json() == []


def test_my_events_requires_organizer(client: TestClient, attendee_headers: dict[str, str]) -> None:
    assert client.get("/api/v1/events/mine").status_code == 401
    assert client.get("/api/v1/events/mine", headers=attendee_headers).status_code == 403


def test_unverified_organizer_cannot_create_event(client: TestClient) -> None:
    user = {
        "email": "new@example.com",
        "password": "s3cretpass",
        "full_name": "New Organizer",
        "role": "organizer",
    }
    client.post("/api/v1/auth/register", json=user)
    login = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post("/api/v1/events", json={}, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Email not verified"
