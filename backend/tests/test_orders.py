from uuid import uuid4

from conftest import create_paid_event, make_headers, place_order
from fastapi.testclient import TestClient


def test_create_order_uses_stored_prices(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={paid_event_id}").json()[0]["id"]
    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": paid_event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": 2, "unit_price_kzt": 1}],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "pending"
    assert data["total_amount_kzt"] == 1000000
    assert data["items"][0]["unit_price_kzt"] == 500000
    assert data["items"][0]["ticket_type_name"] == "Standard"
    assert data["user_id"] is not None

    ticket_type = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    assert ticket_type.json()["reserved_count"] == 2


def test_create_order_requires_sign_in(client: TestClient, paid_event_id: str) -> None:
    assert place_order(client, {}, paid_event_id).status_code == 401


def test_cannot_order_more_than_available(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0, quantity=3)

    res = place_order(client, attendee_headers, event_id, quantity=4)
    assert res.status_code == 409
    assert place_order(client, attendee_headers, event_id, quantity=3).status_code == 201
    assert place_order(client, attendee_headers, event_id).status_code == 409


def test_cannot_order_for_unpublished_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["id"]
    client.post(f"/api/v1/events/unpublish?event_id={event_id}", headers=organizer_headers)

    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": 1}],
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Event is not open for registration"


def test_ticket_type_must_belong_to_the_event(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    res = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": paid_event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": str(uuid4()), "quantity": 1}],
        },
    )
    assert res.status_code == 404


def test_order_detail_is_visible_to_owner_and_organizer_only(
    client: TestClient,
    paid_event_id: str,
    attendee_headers: dict[str, str],
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
) -> None:
    order_id = place_order(client, attendee_headers, paid_event_id).json()["id"]
    url = f"/api/v1/orders/detail?order_id={order_id}"

    assert client.get(url, headers=attendee_headers).status_code == 200
    assert client.get(url, headers=organizer_headers).status_code == 200
    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert client.get(url).status_code == 401


def test_get_order_detail_not_found(client: TestClient, attendee_headers: dict[str, str]) -> None:
    res = client.get(f"/api/v1/orders/detail?order_id={uuid4()}", headers=attendee_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == "Order not found"


def test_cancel_order_releases_reserved_tickets(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = place_order(client, attendee_headers, paid_event_id, quantity=2).json()
    ticket_type_id = order["items"][0]["ticket_type_id"]

    res = client.post(f"/api/v1/orders/cancel?order_id={order['id']}", headers=attendee_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"
    ticket_type = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    assert ticket_type.json()["reserved_count"] == 0

    repeat_cancel = client.post(
        f"/api/v1/orders/cancel?order_id={order['id']}", headers=attendee_headers
    )
    assert repeat_cancel.status_code == 400
    assert "Cannot cancel an order" in repeat_cancel.json()["detail"]


def test_list_orders_returns_only_own_orders(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    place_order(client, attendee_headers, paid_event_id)
    other_headers = make_headers(client, "bob@example.com", "attendee")
    place_order(client, other_headers, paid_event_id)

    mine = client.get("/api/v1/orders", headers=attendee_headers)
    assert mine.status_code == 200
    assert len(mine.json()) == 1
    assert client.get("/api/v1/orders").status_code == 401
