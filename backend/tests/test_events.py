from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def sample_event_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Almaty Tech Meetup",
        "description": "Tech discussions and networking in Almaty",
        "category": "Technology",
        "venue_name": "Astana Hub Almaty",
        "venue_address": "Al-Farabi 17",
        "start_time": (now + timedelta(days=5)).isoformat(),
        "end_time": (now + timedelta(days=5, hours=3)).isoformat(),
        "timezone": "Asia/Almaty",
        "capacity": 150,
        "visibility": "public",
        "is_assigned_seating": False,
    }


def test_create_event(client: TestClient) -> None:
    payload = sample_event_payload()
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "draft"
    assert data["capacity"] == 150
    assert "id" in data


def test_get_event_detail(client: TestClient) -> None:
    payload = sample_event_payload()
    create_res = client.post("/api/v1/events", json=payload)
    event_id = create_res.json()["id"]

    res = client.get(f"/api/v1/events/detail?event_id={event_id}")
    assert res.status_code == 200
    assert res.json()["id"] == event_id


def test_get_event_detail_not_found(client: TestClient) -> None:
    fake_id = uuid4()
    res = client.get(f"/api/v1/events/detail?event_id={fake_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Event not found"


def test_update_event(client: TestClient) -> None:
    payload = sample_event_payload()
    create_res = client.post("/api/v1/events", json=payload)
    event_id = create_res.json()["id"]

    update_payload = {"title": "Updated Title", "capacity": 200}
    res = client.patch(f"/api/v1/events/update?event_id={event_id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"
    assert res.json()["capacity"] == 200


def test_publish_and_unpublish_event(client: TestClient) -> None:
    payload = sample_event_payload()
    create_res = client.post("/api/v1/events", json=payload)
    event_id = create_res.json()["id"]

    pub_res = client.post(f"/api/v1/events/publish?event_id={event_id}")
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"

    unpub_res = client.post(f"/api/v1/events/unpublish?event_id={event_id}")
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == "unpublished"


def test_cancel_event_and_guard(client: TestClient) -> None:
    payload = sample_event_payload()
    create_res = client.post("/api/v1/events", json=payload)
    event_id = create_res.json()["id"]

    cancel_res = client.post(f"/api/v1/events/cancel?event_id={event_id}")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    bad_update = client.patch(
        f"/api/v1/events/update?event_id={event_id}", json={"title": "Should Fail"}
    )
    assert bad_update.status_code == 400
    assert bad_update.json()["detail"] == "Cannot modify a cancelled event"


def test_duplicate_event(client: TestClient) -> None:
    payload = sample_event_payload()
    create_res = client.post("/api/v1/events", json=payload)
    event_id = create_res.json()["id"]

    res = client.post(f"/api/v1/events/duplicate?event_id={event_id}")
    assert res.status_code == 201
    dup_data = res.json()
    assert dup_data["id"] != event_id
    assert dup_data["title"] == f"{payload['title']} (Copy)"
    assert dup_data["status"] == "draft"


def test_list_events(client: TestClient) -> None:
    payload1 = sample_event_payload()
    client.post("/api/v1/events", json=payload1)

    payload2 = sample_event_payload()
    payload2["title"] = "Published Concert"
    res2 = client.post("/api/v1/events", json=payload2)
    id2 = res2.json()["id"]
    client.post(f"/api/v1/events/publish?event_id={id2}")

    list_res = client.get("/api/v1/events")
    assert list_res.status_code == 200
    titles = [e["title"] for e in list_res.json()]
    assert "Published Concert" in titles
