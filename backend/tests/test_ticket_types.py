from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

import core
from features.ticket_types.models import TicketType
from features.ticket_types.service import ticket_type_service


def create_event(client: TestClient, headers: dict[str, str], capacity: int = 100) -> str:
    venue = client.post(
        "/api/v1/venues",
        json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"},
        headers=headers,
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
        headers=headers,
    )
    event_id = res.json()["id"]
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=headers)
    return event_id


def test_create_ticket_type(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "price": 500000, "quantity": 80, "max_per_order": 4},
        headers=organizer_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["event_id"] == event_id
    assert data["available"] == 80
    assert data["sold_count"] == 0


def test_create_free_ticket_type(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Free", "quantity": 10},
        headers=organizer_headers,
    )
    assert res.status_code == 201
    assert res.json()["price"] == 0


def test_ticket_quantity_cannot_exceed_capacity(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers, capacity=50)
    client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 40},
        headers=organizer_headers,
    )

    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "VIP", "quantity": 20},
        headers=organizer_headers,
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Ticket quantity exceeds event capacity"


def test_cannot_add_ticket_type_to_cancelled_event(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers)
    client.post(f"/api/v1/events/cancel?event_id={event_id}", headers=organizer_headers)

    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Late", "quantity": 5},
        headers=organizer_headers,
    )
    assert res.status_code == 400


def test_update_ticket_type(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers, capacity=50)
    create_res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 20},
        headers=organizer_headers,
    )
    ticket_type_id = create_res.json()["id"]

    res = client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={ticket_type_id}",
        json={"price": 300000, "quantity": 50},
        headers=organizer_headers,
    )
    assert res.status_code == 200
    assert res.json()["price"] == 300000
    assert res.json()["available"] == 50

    too_many = client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={ticket_type_id}",
        json={"quantity": 51},
        headers=organizer_headers,
    )
    assert too_many.status_code == 400


def test_hidden_ticket_types_not_listed(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers)
    client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 10},
        headers=organizer_headers,
    )
    hidden = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Staff", "quantity": 5},
        headers=organizer_headers,
    )
    client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={hidden.json()['id']}",
        json={"is_hidden": True},
        headers=organizer_headers,
    )

    public = client.get(f"/api/v1/ticket-types?event_id={event_id}")
    assert [t["name"] for t in public.json()] == ["Standard"]

    anonymous_all = client.get(f"/api/v1/ticket-types?event_id={event_id}&include_hidden=true")
    assert [t["name"] for t in anonymous_all.json()] == ["Standard"]

    everything = client.get(
        f"/api/v1/ticket-types?event_id={event_id}&include_hidden=true",
        headers=organizer_headers,
    )
    assert len(everything.json()) == 2


def test_ticket_type_not_found(client: TestClient) -> None:
    res = client.get(
        "/api/v1/ticket-types/detail?ticket_type_id=00000000-0000-0000-0000-000000000000"
    )
    assert res.status_code == 404


def create_ticket_type(client: TestClient, headers: dict[str, str], quantity: int) -> UUID:
    event_id = create_event(client, headers)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": quantity},
        headers=headers,
    )
    return UUID(res.json()["id"])


def test_reserve_and_confirm_sale(client: TestClient, organizer_headers: dict[str, str]) -> None:
    ticket_type_id = create_ticket_type(client, organizer_headers, quantity=10)

    with core.Session(core.engine) as db:
        assert ticket_type_service.reserve(db, ticket_type_id, 3)
        assert ticket_type_service.confirm_sale(db, ticket_type_id, 2)
        assert ticket_type_service.release(db, ticket_type_id, 1)
        db.commit()

    res = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    data = res.json()
    assert data["reserved_count"] == 0
    assert data["sold_count"] == 2
    assert data["available"] == 8


def test_reserve_rejects_when_sold_out(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    ticket_type_id = create_ticket_type(client, organizer_headers, quantity=2)

    with core.Session(core.engine) as db:
        assert ticket_type_service.reserve(db, ticket_type_id, 2)
        assert not ticket_type_service.reserve(db, ticket_type_id, 1)
        db.commit()
        ticket_type = db.get(TicketType, ticket_type_id)
        assert ticket_type is not None
        assert ticket_type.available == 0


def test_confirm_sale_needs_reservation(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    ticket_type_id = create_ticket_type(client, organizer_headers, quantity=5)

    with core.Session(core.engine) as db:
        assert not ticket_type_service.confirm_sale(db, ticket_type_id, 1)


def test_create_ticket_type_requires_token(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}", json={"name": "Standard", "quantity": 10}
    )
    assert res.status_code == 401


def test_attendee_cannot_create_ticket_type(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers)
    res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 10},
        headers=attendee_headers,
    )
    assert res.status_code == 403


def test_other_organizer_cannot_touch_ticket_types(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
) -> None:
    event_id = create_event(client, organizer_headers)
    created = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 10},
        headers=organizer_headers,
    )

    create_res = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "VIP", "quantity": 5},
        headers=other_organizer_headers,
    )
    assert create_res.status_code == 404

    update_res = client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={created.json()['id']}",
        json={"price": 1},
        headers=other_organizer_headers,
    )
    assert update_res.status_code == 404
