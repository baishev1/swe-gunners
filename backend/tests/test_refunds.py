from conftest import make_headers, place_order
from fastapi.testclient import TestClient


def pay_order(client: TestClient, headers: dict[str, str], order_id: str) -> None:
    res = client.post(
        "/api/v1/payments/simulate",
        headers=headers,
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert res.status_code == 200


def refund(client: TestClient, headers: dict[str, str], order_id: str):
    return client.post(f"/api/v1/orders/refund?order_id={order_id}", headers=headers)


def test_organizer_refunds_paid_order(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id, quantity=2).json()
    pay_order(client, attendee_headers, order["id"])
    ticket_type_id = order["items"][0]["ticket_type_id"]

    res = refund(client, organizer_headers, order["id"])
    assert res.status_code == 200, res.json()
    assert res.json()["status"] == "refunded"

    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    assert [ticket["status"] for ticket in tickets] == ["refunded", "refunded"]

    payment = client.get(
        f"/api/v1/payments/detail?order_id={order['id']}", headers=organizer_headers
    ).json()
    assert payment["status"] == "refunded"

    ticket_type = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    assert ticket_type.json()["sold_count"] == 0
    assert ticket_type.json()["available"] == 100

    timeline = client.get(
        f"/api/v1/audit-log/timeline?event_id={paid_event_id}", headers=organizer_headers
    ).json()
    assert "order_refunded" in [entry["action"] for entry in timeline]

    again = refund(client, organizer_headers, order["id"])
    assert again.status_code == 400
    assert "Cannot refund" in again.json()["detail"]

    ticket_type = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    assert ticket_type.json()["sold_count"] == 0


def test_refund_access(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    pay_order(client, attendee_headers, order["id"])

    assert refund(client, {}, order["id"]).status_code == 401
    assert refund(client, attendee_headers, order["id"]).status_code == 404
    assert refund(client, other_organizer_headers, order["id"]).status_code == 404
    assert refund(client, admin_headers, order["id"]).status_code == 200


def test_pending_order_cannot_be_refunded(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()

    res = refund(client, organizer_headers, order["id"])
    assert res.status_code == 400
    assert "Cannot refund" in res.json()["detail"]


def test_organizer_lists_event_orders(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    other_attendee = make_headers(client, "bob@example.com", "attendee")
    first = place_order(client, attendee_headers, paid_event_id).json()
    second = place_order(client, other_attendee, paid_event_id).json()

    url = f"/api/v1/orders/manage?event_id={paid_event_id}"
    result = client.get(url, headers=organizer_headers)
    assert result.status_code == 200
    assert {order["id"] for order in result.json()} == {first["id"], second["id"]}

    assert client.get(url).status_code == 401
    assert client.get(url, headers=attendee_headers).status_code == 404
    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert client.get(url, headers=admin_headers).status_code == 200


def test_cancelling_event_refunds_paid_and_cancels_pending_orders(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    paid = place_order(client, attendee_headers, paid_event_id, quantity=2).json()
    pay_order(client, attendee_headers, paid["id"])
    pending = place_order(client, attendee_headers, paid_event_id).json()

    res = client.post(f"/api/v1/events/cancel?event_id={paid_event_id}", headers=organizer_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

    orders = client.get(
        f"/api/v1/orders/manage?event_id={paid_event_id}", headers=organizer_headers
    ).json()
    assert {o["id"]: o["status"] for o in orders} == {
        paid["id"]: "refunded",
        pending["id"]: "cancelled",
    }
    tickets = client.get(f"/api/v1/tickets?order_id={paid['id']}", headers=attendee_headers).json()
    assert [t["status"] for t in tickets] == ["refunded", "refunded"]
    ticket_type = client.get(f"/api/v1/ticket-types?event_id={paid_event_id}").json()[0]
    assert ticket_type["sold_count"] == 0
    assert ticket_type["reserved_count"] == 0
