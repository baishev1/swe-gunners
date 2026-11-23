from types import SimpleNamespace

from conftest import create_paid_event, make_headers, place_order
from fastapi.testclient import TestClient

from features.tickets.service import ticket_service


def create_free_order(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> dict:
    event_id = create_paid_event(client, organizer_headers, price=0)
    res = place_order(client, attendee_headers, event_id, quantity=2)
    assert res.status_code == 201
    return res.json()


def test_auto_issue_tickets_on_free_order(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    assert order["status"] == "paid"

    tickets_res = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers)
    assert tickets_res.status_code == 200
    tickets = tickets_res.json()
    assert len(tickets) == 2
    for t in tickets:
        assert t["status"] == "valid"
        assert t["attendee_name"] == "Arman Bekov"
        assert t["attendee_email"] == "arman@example.kz"
        assert len(t["qr_token"]) == 64


def test_get_ticket_detail(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    ticket_id = tickets[0]["id"]

    res = client.get(f"/api/v1/tickets/detail?ticket_id={ticket_id}", headers=attendee_headers)
    assert res.status_code == 200
    assert res.json()["id"] == ticket_id


def test_verify_ticket_valid_and_not_found(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    valid_token = tickets[0]["qr_token"]

    verify_res = client.get(
        "/api/v1/tickets/verify",
        headers=organizer_headers,
        params={"qr_token": valid_token, "event_id": order["event_id"]},
    )
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["valid"] is True
    assert data["status"] == "valid"
    assert data["ticket"]["id"] == tickets[0]["id"]

    fake_res = client.get(
        "/api/v1/tickets/verify",
        headers=organizer_headers,
        params={"qr_token": "nonexistenttoken", "event_id": order["event_id"]},
    )
    assert fake_res.status_code == 200
    fake_data = fake_res.json()
    assert fake_data["valid"] is False
    assert fake_data["status"] == "not_found"


def test_check_in_and_undo_check_in(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    ticket_id = tickets[0]["id"]
    token = tickets[0]["qr_token"]

    params = {"event_id": order["event_id"], "ticket_id": ticket_id}
    check_in_res = client.post("/api/v1/tickets/check-in", headers=organizer_headers, params=params)
    assert check_in_res.status_code == 200
    assert check_in_res.json()["status"] == "checked_in"
    assert check_in_res.json()["checked_in_at"] is not None

    repeat_check_in = client.post(
        "/api/v1/tickets/check-in", headers=organizer_headers, params=params
    )
    assert repeat_check_in.status_code == 400
    assert "already checked in" in repeat_check_in.json()["detail"]

    verify_res = client.get(
        "/api/v1/tickets/verify",
        headers=organizer_headers,
        params={"event_id": order["event_id"], "qr_token": token},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is False
    assert verify_res.json()["status"] == "checked_in"

    undo_res = client.post(
        "/api/v1/tickets/undo-check-in", headers=organizer_headers, params=params
    )
    assert undo_res.status_code == 200
    assert undo_res.json()["status"] == "valid"
    assert undo_res.json()["checked_in_at"] is None


def test_download_ticket_pdf(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()
    ticket_id = tickets[0]["id"]

    pdf_res = client.get(f"/api/v1/tickets/pdf?ticket_id={ticket_id}", headers=attendee_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")


def test_tickets_are_private_to_the_order_owner(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    ticket_id = client.get(
        f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers
    ).json()[0]["id"]
    other_headers = make_headers(client, "bob@example.com", "attendee")

    assert client.get(f"/api/v1/tickets?event_id={order['event_id']}").status_code == 401
    assert client.get(f"/api/v1/tickets?order_id={order['id']}", headers=other_headers).json() == []
    assert (
        client.get(
            f"/api/v1/tickets/detail?ticket_id={ticket_id}", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.get(f"/api/v1/tickets/pdf?ticket_id={ticket_id}", headers=other_headers).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/tickets/pdf?ticket_id={ticket_id}", headers=organizer_headers
        ).status_code
        == 200
    )


def test_ticket_qr_svg_encodes_the_admission_token(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    order = create_free_order(client, organizer_headers, attendee_headers)
    ticket = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers).json()[
        0
    ]

    res = client.get(f"/api/v1/tickets/qr?ticket_id={ticket['id']}", headers=attendee_headers)

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    # Same token the PDF and the scanner use, drawn in black (not the purple Campaign QR).
    expected = ticket_service.build_qr_svg(SimpleNamespace(qr_token=ticket["qr_token"]))  # type: ignore[arg-type]
    assert res.text == expected
    assert 'fill="#000000"' in res.text

    other_headers = make_headers(client, "qr-other@example.com", "attendee")
    other = client.get(f"/api/v1/tickets/qr?ticket_id={ticket['id']}", headers=other_headers)
    assert other.status_code == 404
