from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def create_event(client: TestClient, capacity: int = 100) -> str:
    venue = client.post(
        "/api/v1/venues", json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"}
    )
    now = datetime.now(UTC)
    res = client.post(
        "/api/v1/events",
        json={
            "title": "Almaty Tech Meetup",
            "category": "Technology",
            "venue_id": venue.json()["id"],
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=3)).isoformat(),
            "capacity": capacity,
        },
    )
    return res.json()["id"]


def test_create_ticket_type(client: TestClient) -> None:
    event_id = create_event(client)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "price": 500000, "quantity": 80, "max_per_order": 4},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["event_id"] == event_id
    assert data["available"] == 80
    assert data["sold_count"] == 0


def test_create_free_ticket_type(client: TestClient) -> None:
    event_id = create_event(client)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Free", "quantity": 10}
    )
    assert res.status_code == 201
    assert res.json()["price"] == 0


def test_ticket_quantity_cannot_exceed_capacity(client: TestClient) -> None:
    event_id = create_event(client, capacity=50)
    client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Standard", "quantity": 40}
    )

    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "VIP", "quantity": 20}
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Ticket quantity exceeds event capacity"


def test_cannot_add_ticket_type_to_cancelled_event(client: TestClient) -> None:
    event_id = create_event(client)
    client.post(f"/api/v1/events/cancel?event_id={event_id}")

    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Late", "quantity": 5}
    )
    assert res.status_code == 400


def test_update_ticket_type(client: TestClient) -> None:
    event_id = create_event(client, capacity=50)
    create_res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Standard", "quantity": 20}
    )
    ticket_type_id = create_res.json()["id"]

    res = client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={ticket_type_id}",
        json={"price": 300000, "quantity": 50},
    )
    assert res.status_code == 200
    assert res.json()["price"] == 300000
    assert res.json()["available"] == 50

    too_many = client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={ticket_type_id}", json={"quantity": 51}
    )
    assert too_many.status_code == 400


def test_hidden_ticket_types_not_listed(client: TestClient) -> None:
    event_id = create_event(client)
    client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Standard", "quantity": 10}
    )
    hidden = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Staff", "quantity": 5}
    )
    client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={hidden.json()['id']}",
        json={"is_hidden": True},
    )

    public = client.get(f"/api/v1/ticket-types?event_id={event_id}")
    assert [t["name"] for t in public.json()] == ["Standard"]

    everything = client.get(f"/api/v1/ticket-types?event_id={event_id}&include_hidden=true")
    assert len(everything.json()) == 2


def test_ticket_type_not_found(client: TestClient) -> None:
    res = client.get(
        "/api/v1/ticket-types/detail?ticket_type_id=00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404
