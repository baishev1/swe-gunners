from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select

import core
from features.orders.models import Order
from features.promo.models import PromoRedemption
from features.tickets.models import Ticket

ANALYTICS = "/api/v1/analytics/event"


def ticket_type_id(client: TestClient, event_id: str, headers: dict[str, str]) -> str:
    res = client.get(
        "/api/v1/ticket-types",
        params={"event_id": event_id, "include_hidden": True},
        headers=headers,
    )
    return res.json()[0]["id"]


def buy(
    client: TestClient,
    headers: dict[str, str],
    event_id: str,
    type_id: str,
    quantity: int,
    pay: bool = True,
) -> str:
    """Buys as a signed-in attendee; the server prices the order from the ticket type."""
    order = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": event_id,
            "customer_name": "Aigerim",
            "customer_email": "aigerim@example.kz",
            "items": [{"ticket_type_id": type_id, "quantity": quantity}],
        },
    )
    assert order.status_code == 201, order.json()
    order_id = order.json()["id"]
    if pay:
        payment = client.post(
            "/api/v1/payments/simulate",
            headers=headers,
            json={"order_id": order_id, "simulate_failure": False},
        )
        assert payment.json()["status"] == "succeeded", payment.json()
    return order_id


def test_analytics_totals(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    # Other test modules change the platform rate, so pin it before asserting fees.
    client.patch(
        "/api/v1/admin/settings",
        json={"processing_fee_percent": 3.0},
        headers=admin_headers,
    )
    type_id = ticket_type_id(client, paid_event_id, organizer_headers)
    campaign = client.post(
        f"/api/v1/promo/campaigns?event_id={paid_event_id}",
        json={"name": "Instagram", "discount_type": "percent", "discount_value": 10},
        headers=organizer_headers,
    ).json()

    promo_order = buy(client, attendee_headers, paid_event_id, type_id, 2)
    refunded_order = buy(client, attendee_headers, paid_event_id, type_id, 1)
    buy(client, attendee_headers, paid_event_id, type_id, 5, pay=False)  # pending, never counted

    with core.Session(core.engine) as db:
        db.add(
            PromoRedemption(
                campaign_id=UUID(campaign["id"]),
                order_id=UUID(promo_order),
                discount_amount=100000,
            )
        )
        refunded = db.get(Order, UUID(refunded_order))
        assert refunded is not None
        refunded.status = "refunded"
        ticket = db.scalars(select(Ticket).where(Ticket.order_id == UUID(promo_order))).first()
        assert ticket is not None
        ticket.status = "checked_in"
        ticket.checked_in_at = datetime.now(UTC)
        db.commit()

    res = client.get(ANALYTICS, params={"event_id": paid_event_id}, headers=organizer_headers)
    assert res.status_code == 200, res.json()
    data = res.json()

    assert data["capacity"] == {
        "total_capacity": 100,
        "tickets_sold": 2,
        "tickets_remaining": 98,
        "percent_sold": 2.0,
    }
    assert data["revenue"] == {
        "gross_sales": 1500000,
        "discounts": 100000,
        "refunds": 500000,
        "net_revenue": 900000,
        "processing_fees": 27000,
        "estimated_payout": 873000,
    }
    assert data["attendance"] == {"checked_in": 1, "absent": 1, "percent_checked_in": 50.0}

    [standard] = data["ticket_types"]
    assert standard["ticket_type_id"] == type_id
    assert standard["tickets_sold"] == 2
    assert standard["gross_sales"] == 1500000
    assert standard["checked_in"] == 1

    [instagram] = data["campaigns"]
    assert instagram["code"] == campaign["code"]
    assert instagram["redemptions"] == 1
    assert instagram["tickets"] == 2
    assert instagram["discounts"] == 100000
    assert instagram["revenue"] == 900000

    [day] = data["sales_over_time"]
    assert day["orders"] == 2
    assert day["tickets"] == 3
    assert day["gross_sales"] == 1500000


def test_analytics_filters(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    type_id = ticket_type_id(client, paid_event_id, organizer_headers)
    buy(client, attendee_headers, paid_event_id, type_id, 3)

    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    later = client.get(
        ANALYTICS,
        params={"event_id": paid_event_id, "date_from": future},
        headers=organizer_headers,
    ).json()
    assert later["capacity"]["tickets_sold"] == 0
    assert later["sales_over_time"] == []

    by_type = client.get(
        ANALYTICS,
        params={"event_id": paid_event_id, "ticket_type_id": type_id},
        headers=organizer_headers,
    ).json()
    assert by_type["capacity"]["tickets_sold"] == 3

    bad_range = client.get(
        ANALYTICS,
        params={"event_id": paid_event_id, "date_from": future, "date_to": future},
        headers=organizer_headers,
    )
    assert bad_range.status_code == 400

    other_event = client.get(
        ANALYTICS,
        params={"event_id": paid_event_id, "ticket_type_id": paid_event_id},
        headers=organizer_headers,
    )
    assert other_event.status_code == 404


def test_analytics_access(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    params = {"event_id": paid_event_id}
    assert client.get(ANALYTICS, params=params).status_code == 401
    assert client.get(ANALYTICS, params=params, headers=attendee_headers).status_code == 404
    assert client.get(ANALYTICS, params=params, headers=other_organizer_headers).status_code == 404
    assert client.get(ANALYTICS, params=params, headers=organizer_headers).status_code == 200
    assert client.get(ANALYTICS, params=params, headers=admin_headers).status_code == 200


def test_analytics_without_sales(
    client: TestClient, organizer_headers: dict[str, str], make_paid_event
) -> None:
    event_id = make_paid_event()
    data = client.get(ANALYTICS, params={"event_id": event_id}, headers=organizer_headers).json()
    assert data["capacity"]["percent_sold"] == 0.0
    assert data["revenue"]["net_revenue"] == 0
    assert data["attendance"]["percent_checked_in"] == 0.0
    assert data["campaigns"] == []
