from uuid import uuid4

from fastapi.testclient import TestClient


def create_free_order(client: TestClient) -> dict:
    payload = {
        "event_id": str(uuid4()),
        "customer_name": "Saule Omarova",
        "customer_email": "saule@example.kz",
        "items": [
            {
                "ticket_type_id": str(uuid4()),
                "ticket_type_name": "Free Entry",
                "unit_price_kzt": 0,
                "quantity": 2,
            }
        ],
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 201
    return res.json()


def test_auto_issue_tickets_on_free_order(client: TestClient) -> None:
    order = create_free_order(client)
    assert order["status"] == "paid"

    tickets_res = client.get(f"/api/v1/tickets?order_id={order['id']}")
    assert tickets_res.status_code == 200
    tickets = tickets_res.json()
    assert len(tickets) == 2
    for t in tickets:
        assert t["status"] == "valid"
        assert t["attendee_name"] == "Saule Omarova"
        assert t["attendee_email"] == "saule@example.kz"
        assert len(t["qr_token"]) == 64


def test_get_ticket_detail(client: TestClient) -> None:
    order = create_free_order(client)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}").json()
    ticket_id = tickets[0]["id"]

    res = client.get(f"/api/v1/tickets/detail?ticket_id={ticket_id}")
    assert res.status_code == 200
    assert res.json()["id"] == ticket_id


def test_verify_ticket_valid_and_not_found(client: TestClient) -> None:
    order = create_free_order(client)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}").json()
    valid_token = tickets[0]["qr_token"]

    verify_res = client.get(f"/api/v1/tickets/verify?qr_token={valid_token}")
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["valid"] is True
    assert data["status"] == "valid"
    assert data["ticket"]["id"] == tickets[0]["id"]

    fake_res = client.get("/api/v1/tickets/verify?qr_token=nonexistenttoken")
    assert fake_res.status_code == 200
    fake_data = fake_res.json()
    assert fake_data["valid"] is False
    assert fake_data["status"] == "not_found"


def test_check_in_and_undo_check_in(client: TestClient) -> None:
    order = create_free_order(client)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}").json()
    ticket_id = tickets[0]["id"]
    token = tickets[0]["qr_token"]

    check_in_res = client.post(f"/api/v1/tickets/check-in?ticket_id={ticket_id}")
    assert check_in_res.status_code == 200
    assert check_in_res.json()["status"] == "checked_in"
    assert check_in_res.json()["checked_in_at"] is not None

    repeat_check_in = client.post(f"/api/v1/tickets/check-in?ticket_id={ticket_id}")
    assert repeat_check_in.status_code == 400
    assert "already checked in" in repeat_check_in.json()["detail"]

    verify_res = client.get(f"/api/v1/tickets/verify?qr_token={token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is False
    assert verify_res.json()["status"] == "checked_in"

    undo_res = client.post(f"/api/v1/tickets/undo-check-in?ticket_id={ticket_id}")
    assert undo_res.status_code == 200
    assert undo_res.json()["status"] == "valid"
    assert undo_res.json()["checked_in_at"] is None


def test_download_ticket_pdf(client: TestClient) -> None:
    order = create_free_order(client)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}").json()
    ticket_id = tickets[0]["id"]

    pdf_res = client.get(f"/api/v1/tickets/pdf?ticket_id={ticket_id}")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")
