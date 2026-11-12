from conftest import make_headers, place_order
from fastapi.testclient import TestClient


def create_paid_order(client: TestClient, headers: dict[str, str], event_id: str) -> dict:
    res = place_order(client, headers, event_id, quantity=2)
    assert res.status_code == 201
    return res.json()


def test_simulate_payment_failure(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = create_paid_order(client, attendee_headers, paid_event_id)
    order_id = order["id"]
    assert order["status"] == "pending"

    pay_res = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order_id, "simulate_failure": True},
    )
    assert pay_res.status_code == 200
    payment = pay_res.json()
    assert payment["status"] == "failed"
    assert payment["amount_kzt"] == 1000000

    order_check = client.get(
        f"/api/v1/orders/detail?order_id={order_id}", headers=attendee_headers
    ).json()
    assert order_check["status"] == "pending"

    tickets_res = client.get(f"/api/v1/tickets?order_id={order_id}", headers=attendee_headers)
    assert tickets_res.status_code == 200
    assert len(tickets_res.json()) == 0


def test_simulate_payment_success_and_ticket_issuance(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = create_paid_order(client, attendee_headers, paid_event_id)
    order_id = order["id"]

    pay_res = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert pay_res.status_code == 200
    payment = pay_res.json()
    assert payment["status"] == "succeeded"
    assert payment["amount_kzt"] == 1000000
    assert payment["provider"] == "simulation"
    assert payment["transaction_id"].startswith("sim_")

    order_check = client.get(
        f"/api/v1/orders/detail?order_id={order_id}", headers=attendee_headers
    ).json()
    assert order_check["status"] == "paid"

    tickets = client.get(f"/api/v1/tickets?order_id={order_id}", headers=attendee_headers).json()
    assert len(tickets) == 2
    for t in tickets:
        assert t["status"] == "valid"
        assert t["attendee_name"] == "Arman Bekov"

    repeat_pay = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert repeat_pay.status_code == 400
    assert "cannot be paid" in repeat_pay.json()["detail"]


def test_get_payment_detail(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = create_paid_order(client, attendee_headers, paid_event_id)
    order_id = order["id"]

    client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order_id, "simulate_failure": False},
    )

    detail_res = client.get(
        f"/api/v1/payments/detail?order_id={order_id}", headers=attendee_headers
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["order_id"] == order_id
    assert detail_res.json()["status"] == "succeeded"


def test_payment_moves_tickets_from_reserved_to_sold(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = create_paid_order(client, attendee_headers, paid_event_id)
    client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )

    ticket_type_id = order["items"][0]["ticket_type_id"]
    ticket_type = client.get(f"/api/v1/ticket-types/detail?ticket_type_id={ticket_type_id}")
    assert ticket_type.json()["reserved_count"] == 0
    assert ticket_type.json()["sold_count"] == 2


def test_cannot_pay_someone_elses_order(
    client: TestClient, paid_event_id: str, attendee_headers: dict[str, str]
) -> None:
    order = create_paid_order(client, attendee_headers, paid_event_id)
    other_headers = make_headers(client, "bob@example.com", "attendee")

    res = client.post(
        "/api/v1/payments/simulate",
        headers=other_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )
    assert res.status_code == 404
