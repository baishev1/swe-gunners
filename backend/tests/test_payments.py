from uuid import uuid4

from fastapi.testclient import TestClient


def create_paid_order(client: TestClient) -> dict:
    payload = {
        "event_id": str(uuid4()),
        "customer_name": "Daulet Sarsenov",
        "customer_email": "daulet@example.kz",
        "items": [
            {
                "ticket_type_id": str(uuid4()),
                "ticket_type_name": "Conference Pass",
                "unit_price_kzt": 10000,
                "quantity": 2,
            }
        ],
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 201
    return res.json()


def test_simulate_payment_failure(client: TestClient) -> None:
    order = create_paid_order(client)
    order_id = order["id"]
    assert order["status"] == "pending"

    pay_res = client.post(
        "/api/v1/payments/simulate",
        json={"order_id": order_id, "simulate_failure": True},
    )
    assert pay_res.status_code == 200
    payment = pay_res.json()
    assert payment["status"] == "failed"
    assert payment["amount_kzt"] == 20000

    order_check = client.get(f"/api/v1/orders/detail?order_id={order_id}").json()
    assert order_check["status"] == "pending"

    tickets_res = client.get(f"/api/v1/tickets?order_id={order_id}")
    assert tickets_res.status_code == 200
    assert len(tickets_res.json()) == 0


def test_simulate_payment_success_and_ticket_issuance(client: TestClient) -> None:
    order = create_paid_order(client)
    order_id = order["id"]

    pay_res = client.post(
        "/api/v1/payments/simulate",
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert pay_res.status_code == 200
    payment = pay_res.json()
    assert payment["status"] == "succeeded"
    assert payment["amount_kzt"] == 20000
    assert payment["provider"] == "simulation"
    assert payment["transaction_id"].startswith("sim_")

    order_check = client.get(f"/api/v1/orders/detail?order_id={order_id}").json()
    assert order_check["status"] == "paid"

    tickets = client.get(f"/api/v1/tickets?order_id={order_id}").json()
    assert len(tickets) == 2
    for t in tickets:
        assert t["status"] == "valid"
        assert t["attendee_name"] == "Daulet Sarsenov"

    repeat_pay = client.post(
        "/api/v1/payments/simulate",
        json={"order_id": order_id, "simulate_failure": False},
    )
    assert repeat_pay.status_code == 400
    assert "cannot be paid" in repeat_pay.json()["detail"]


def test_get_payment_detail(client: TestClient) -> None:
    order = create_paid_order(client)
    order_id = order["id"]

    client.post(
        "/api/v1/payments/simulate",
        json={"order_id": order_id, "simulate_failure": False},
    )

    detail_res = client.get(f"/api/v1/payments/detail?order_id={order_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["order_id"] == order_id
    assert detail_res.json()["status"] == "succeeded"
