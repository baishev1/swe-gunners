from datetime import UTC, datetime, timedelta

from conftest import create_paid_event, place_order
from fastapi.testclient import TestClient


def ticket_type_id(client: TestClient, event_id: str) -> str:
    return client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["id"]


def test_attendee_list_shows_registrations(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0, quantity=10)
    order = place_order(client, attendee_headers, event_id, quantity=2).json()

    url = f"/api/v1/tickets/event-attendees?event_id={event_id}"
    res = client.get(url, headers=organizer_headers)
    assert res.status_code == 200
    attendees = res.json()
    assert len(attendees) == 2
    for entry in attendees:
        assert entry["attendee_name"] == "Arman Bekov"
        assert entry["attendee_email"] == "arman@example.kz"
        assert entry["ticket_type_name"] == "Standard"
        assert entry["ticket_status"] == "valid"
        assert entry["order_status"] == "paid"
        assert entry["order_id"] == order["id"]


def test_attendee_list_requires_event_manager(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    place_order(client, attendee_headers, event_id)
    url = f"/api/v1/tickets/event-attendees?event_id={event_id}"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=attendee_headers).status_code == 404
    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert client.get(url, headers=organizer_headers).status_code == 200


def test_ticket_type_counters_track_lifecycle(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0, quantity=10)
    tt_id = ticket_type_id(client, event_id)

    def stats() -> dict:
        return client.get(f"/api/v1/ticket-types/detail?ticket_type_id={tt_id}").json()

    place_order(client, attendee_headers, event_id, quantity=3)
    data = stats()
    assert data["sold_count"] == 3
    assert data["reserved_count"] == 0
    assert data["available"] == 7
    assert data["checked_in_count"] == 0
    assert data["refunded_count"] == 0

    tickets = client.get(f"/api/v1/tickets?event_id={event_id}", headers=attendee_headers).json()
    client.post(
        "/api/v1/tickets/check-in",
        headers=organizer_headers,
        params={"event_id": event_id, "ticket_id": tickets[0]["id"]},
    )
    data = stats()
    assert data["checked_in_count"] == 1
    assert data["sold_count"] == 3


def test_paid_order_cancel_restock_and_cancels_tickets(
    client: TestClient,
    paid_event_id: str,
    attendee_headers: dict[str, str],
    organizer_headers: dict[str, str],
) -> None:
    order = place_order(client, attendee_headers, paid_event_id, quantity=2).json()
    tt_id = order["items"][0]["ticket_type_id"]
    pay = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )
    assert pay.status_code == 200, pay.json()

    def stats() -> dict:
        return client.get(f"/api/v1/ticket-types/detail?ticket_type_id={tt_id}").json()

    assert stats()["sold_count"] == 2
    assert stats()["available"] == 98

    cancel = client.post(f"/api/v1/orders/cancel?order_id={order['id']}", headers=attendee_headers)
    assert cancel.status_code == 200

    data = stats()
    assert data["sold_count"] == 0
    assert data["reserved_count"] == 0
    assert data["available"] == 100
    assert data["refunded_count"] == 2

    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    assert all(t["status"] == "cancelled" for t in tickets)


def test_registration_window_blocks_orders(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    venue = client.post(
        "/api/v1/venues",
        json={"name": "Astana Hub", "address": "Al-Farabi 17"},
        headers=organizer_headers,
    )
    now = datetime.now(UTC)
    event = client.post(
        "/api/v1/events",
        headers=organizer_headers,
        json={
            "title": "Windowed Event",
            "category": "Music",
            "venue_id": venue.json()["id"],
            "start_time": (now + timedelta(days=10)).isoformat(),
            "end_time": (now + timedelta(days=10, hours=2)).isoformat(),
            "capacity": 50,
            "registration_start_time": (now + timedelta(days=1)).isoformat(),
            "registration_end_time": (now + timedelta(days=5)).isoformat(),
        },
    ).json()
    event_id = event["id"]
    tt_id = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "quantity": 10},
        headers=organizer_headers,
    ).json()["id"]
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=organizer_headers)

    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": tt_id, "quantity": 1}],
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Registration has not opened yet"

    client.patch(
        f"/api/v1/events/update?event_id={event_id}",
        json={
            "registration_start_time": (now - timedelta(days=10)).isoformat(),
            "registration_end_time": (now - timedelta(days=1)).isoformat(),
        },
        headers=organizer_headers,
    )
    closed = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": tt_id, "quantity": 1}],
        },
    )
    assert closed.status_code == 400
    assert closed.json()["detail"] == "Registration is closed"


def test_attendee_list_excludes_other_events(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    other_event_id = create_paid_event(client, other_organizer_headers, price=0)
    place_order(client, attendee_headers, event_id)
    place_order(client, attendee_headers, other_event_id)

    res = client.get(
        f"/api/v1/tickets/event-attendees?event_id={event_id}", headers=organizer_headers
    )
    assert len(res.json()) == 1
    assert res.json()[0]["attendee_email"] == "arman@example.kz"
