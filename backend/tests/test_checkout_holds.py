from datetime import timedelta
from uuid import UUID

from conftest import complete_activation_checklist, create_paid_event, place_order
from fastapi.testclient import TestClient
from sqlalchemy import update

import core
from core import Session, settings
from features.orders.models import Order
from features.orders.service import order_service


def age_order(order_id: str, minutes: int) -> None:
    """Moves an order's creation time into the past so its checkout hold runs out."""
    assert core.engine is not None
    with Session(core.engine) as db:
        db.execute(
            update(Order)
            .where(Order.id == UUID(order_id))
            .values(created_at=core.time_now() - timedelta(minutes=minutes))
        )
        db.commit()


def reserved_count(client: TestClient, event_id: str) -> int:
    return client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["reserved_count"]


def test_pending_order_reports_hold_deadline(
    client: TestClient, attendee_headers: dict[str, str], paid_event_id: str
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()

    assert order["status"] == "pending"
    assert order["hold_expires_at"] is not None


def test_abandoned_checkout_releases_stock_for_next_buyer(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    # Free tickets settle instantly, so use a paid event that never gets paid.
    event_id = create_paid_event(client, organizer_headers, price=100000, quantity=2)
    complete_activation_checklist(client, organizer_headers, event_id)
    client.post(f"/api/v1/paid-sales/activate?event_id={event_id}", headers=organizer_headers)

    abandoned = place_order(client, attendee_headers, event_id, quantity=2).json()
    assert place_order(client, attendee_headers, event_id).status_code == 409

    age_order(abandoned["id"], settings.ORDER_HOLD_MINUTES + 1)
    fresh = place_order(client, attendee_headers, event_id, quantity=2)

    assert fresh.status_code == 201
    assert reserved_count(client, event_id) == 2
    old = client.get(f"/api/v1/orders/detail?order_id={abandoned['id']}", headers=attendee_headers)
    assert old.json()["status"] == "expired"
    assert old.json()["hold_expires_at"] is None


def test_expired_order_cannot_be_paid(
    client: TestClient, attendee_headers: dict[str, str], paid_event_id: str
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    age_order(order["id"], settings.ORDER_HOLD_MINUTES + 1)

    res = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )

    assert res.status_code == 409
    assert reserved_count(client, paid_event_id) == 0
    tickets = client.get(f"/api/v1/tickets?order_id={order['id']}", headers=attendee_headers)
    assert tickets.json() == []


def test_sweep_leaves_fresh_and_paid_orders_alone(
    client: TestClient, attendee_headers: dict[str, str], paid_event_id: str
) -> None:
    fresh = place_order(client, attendee_headers, paid_event_id).json()
    paid = place_order(client, attendee_headers, paid_event_id).json()
    client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": paid["id"], "simulate_failure": False},
    )
    age_order(paid["id"], settings.ORDER_HOLD_MINUTES + 30)

    assert core.engine is not None
    with Session(core.engine) as db:
        assert order_service.expire_stale_orders(db) == 0

    statuses = {
        o["id"]: o["status"] for o in client.get("/api/v1/orders", headers=attendee_headers).json()
    }
    assert statuses[fresh["id"]] == "pending"
    assert statuses[paid["id"]] == "paid"
    assert reserved_count(client, paid_event_id) == 1
