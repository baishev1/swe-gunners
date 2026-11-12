import logging

from conftest import place_order
from fastapi.testclient import TestClient


def pay_order(
    client: TestClient, headers: dict[str, str], order_id: str, simulate_failure: bool = False
) -> None:
    res = client.post(
        "/api/v1/payments/simulate",
        headers=headers,
        json={"order_id": order_id, "simulate_failure": simulate_failure},
    )
    assert res.status_code == 200


def test_order_confirmation_email(
    client: TestClient,
    attendee_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    with caplog.at_level(logging.INFO):
        pay_order(client, attendee_headers, order["id"])

    assert "Your tickets for Paid Concert" in caplog.text
    assert "arman@example.kz" in caplog.text


def test_payment_failure_email(
    client: TestClient,
    attendee_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    with caplog.at_level(logging.INFO):
        pay_order(client, attendee_headers, order["id"], simulate_failure=True)

    assert "Payment failed for Paid Concert" in caplog.text


def test_refund_and_cancellation_emails(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    pay_order(client, attendee_headers, order["id"])

    with caplog.at_level(logging.INFO):
        refund = client.post(
            f"/api/v1/orders/refund?order_id={order['id']}", headers=organizer_headers
        )
        assert refund.status_code == 200
        assert "Refund issued for Paid Concert" in caplog.text

    caplog.clear()
    pending_order = place_order(client, attendee_headers, paid_event_id).json()
    assert pending_order["status"] == "pending"
    with caplog.at_level(logging.INFO):
        cancel = client.post(
            f"/api/v1/events/cancel?event_id={paid_event_id}", headers=organizer_headers
        )
        assert cancel.status_code == 200
        assert "Event cancelled: Paid Concert" in caplog.text
