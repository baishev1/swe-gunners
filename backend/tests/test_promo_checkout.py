from typing import Any

from conftest import create_paid_event
from fastapi.testclient import TestClient


def create_campaign(
    client: TestClient, headers: dict[str, str], event_id: str, **overrides: Any
) -> dict:
    payload = {"name": "Instagram", "discount_type": "percent", "discount_value": 20}
    res = client.post(
        f"/api/v1/promo/campaigns?event_id={event_id}", json=payload | overrides, headers=headers
    )
    assert res.status_code == 201
    return res.json()


def order_with_code(
    client: TestClient, headers: dict[str, str], event_id: str, code: str | None, quantity: int = 2
):
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["id"]
    return client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": quantity}],
            "promo_code": code,
        },
    )


def pay(client: TestClient, headers: dict[str, str], order_id: str):
    return client.post(
        "/api/v1/payments/simulate",
        headers=headers,
        json={"order_id": order_id, "simulate_failure": False},
    )


def test_promo_code_discounts_order_and_is_redeemed_on_payment(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    campaign = create_campaign(client, organizer_headers, paid_event_id, max_redemptions=5)

    order = order_with_code(client, attendee_headers, paid_event_id, campaign["code"].lower())

    assert order.status_code == 201
    body = order.json()
    # Two tickets at 500000 tiyn, 20% off.
    assert body["discount_kzt"] == 200000
    assert body["total_amount_kzt"] == 800000
    assert body["promo_campaign_id"] == campaign["id"]

    payment = pay(client, attendee_headers, body["id"])
    assert payment.status_code == 200
    assert payment.json()["amount_kzt"] == 800000

    detail = client.get(
        f"/api/v1/promo/campaigns/detail?campaign_id={campaign['id']}", headers=organizer_headers
    )
    assert detail.json()["redemption_count"] == 1
    analytics = client.get(
        f"/api/v1/analytics/event?event_id={paid_event_id}", headers=organizer_headers
    ).json()
    assert analytics["revenue"]["discounts"] == 200000
    assert analytics["campaigns"][0]["redemptions"] == 1


def test_unknown_or_exhausted_promo_code_is_rejected(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    assert order_with_code(client, attendee_headers, paid_event_id, "NOPE1234").status_code == 400

    campaign = create_campaign(client, organizer_headers, paid_event_id, max_redemptions=1)
    first = order_with_code(client, attendee_headers, paid_event_id, campaign["code"]).json()
    assert pay(client, attendee_headers, first["id"]).status_code == 200

    res = order_with_code(client, attendee_headers, paid_event_id, campaign["code"])
    assert res.status_code == 400
    assert "limit" in res.json()["detail"]


def test_last_redemption_cannot_be_taken_twice(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    campaign = create_campaign(client, organizer_headers, paid_event_id, max_redemptions=1)
    first = order_with_code(client, attendee_headers, paid_event_id, campaign["code"]).json()
    second = order_with_code(client, attendee_headers, paid_event_id, campaign["code"]).json()

    assert pay(client, attendee_headers, first["id"]).status_code == 200
    res = pay(client, attendee_headers, second["id"])

    assert res.status_code == 409
    order = client.get(f"/api/v1/orders/detail?order_id={second['id']}", headers=attendee_headers)
    assert order.json()["status"] == "pending"


def test_full_discount_on_free_total_issues_tickets_immediately(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    campaign = create_campaign(
        client, organizer_headers, event_id, discount_type="fixed", discount_value=1000
    )

    res = order_with_code(client, attendee_headers, event_id, campaign["code"])

    assert res.status_code == 201
    assert res.json()["status"] == "paid"
    assert res.json()["discount_kzt"] == 0
