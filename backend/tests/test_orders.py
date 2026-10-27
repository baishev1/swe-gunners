from uuid import uuid4

from fastapi.testclient import TestClient


def sample_order_payload(event_id: str | None = None, user_id: str | None = None) -> dict:
    return {
        "event_id": event_id or str(uuid4()),
        "user_id": user_id or str(uuid4()),
        "customer_name": "Arman Bekov",
        "customer_email": "arman@example.kz",
        "items": [
            {
                "ticket_type_id": str(uuid4()),
                "ticket_type_name": "Standard Admission",
                "unit_price_kzt": 5000,
                "quantity": 2,
            },
            {
                "ticket_type_id": str(uuid4()),
                "ticket_type_name": "VIP Pass",
                "unit_price_kzt": 15000,
                "quantity": 1,
            },
        ],
    }


def test_create_order(client: TestClient) -> None:
    payload = sample_order_payload()
    res = client.post("/orders", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["customer_name"] == payload["customer_name"]
    assert data["customer_email"] == payload["customer_email"]
    assert data["status"] == "pending"
    assert data["total_amount_kzt"] == 25000
    assert len(data["items"]) == 2
    assert "id" in data


def test_get_order_detail(client: TestClient) -> None:
    payload = sample_order_payload()
    create_res = client.post("/orders", json=payload)
    order_id = create_res.json()["id"]

    res = client.get(f"/orders/detail?order_id={order_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == order_id
    assert len(data["items"]) == 2


def test_get_order_detail_not_found(client: TestClient) -> None:
    fake_id = uuid4()
    res = client.get(f"/orders/detail?order_id={fake_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == "Order not found"


def test_cancel_order(client: TestClient) -> None:
    payload = sample_order_payload()
    create_res = client.post("/orders", json=payload)
    order_id = create_res.json()["id"]

    res = client.post(f"/orders/cancel?order_id={order_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

    repeat_cancel = client.post(f"/orders/cancel?order_id={order_id}")
    assert repeat_cancel.status_code == 400
    assert "Cannot cancel an order" in repeat_cancel.json()["detail"]


def test_list_orders(client: TestClient) -> None:
    user_id = str(uuid4())
    event_id = str(uuid4())
    payload = sample_order_payload(event_id=event_id, user_id=user_id)
    client.post("/orders", json=payload)

    res_all = client.get("/orders")
    assert res_all.status_code == 200
    assert any(o["customer_email"] == "arman@example.kz" for o in res_all.json())

    res_user = client.get(f"/orders?user_id={user_id}")
    assert res_user.status_code == 200
    assert len(res_user.json()) >= 1
    assert all(o["user_id"] == user_id for o in res_user.json())
