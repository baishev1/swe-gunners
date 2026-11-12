import csv
from datetime import UTC, datetime, timedelta
from io import StringIO
from uuid import UUID

from fastapi.testclient import TestClient

import core
from features.orders.models import Order


def place_order(
    client: TestClient, event_id: str, email: str, name: str = "Aigerim", fail: bool = False
) -> str:
    order = client.post(
        "/api/v1/orders",
        json={
            "event_id": event_id,
            "customer_name": name,
            "customer_email": email,
            "items": [
                {
                    "ticket_type_id": "00000000-0000-0000-0000-000000000001",
                    "ticket_type_name": "Standard",
                    "unit_price_kzt": 250000,
                    "quantity": 2,
                }
            ],
        },
    )
    assert order.status_code == 201, order.json()
    order_id = order.json()["id"]
    client.post("/api/v1/payments/simulate", json={"order_id": order_id, "simulate_failure": fail})
    return order_id


def test_ops_routes_need_platform_admin(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    for path in ("/orders", "/payments", "/monitoring", "/reports/export?report=orders"):
        assert client.get(f"/api/v1/admin{path}").status_code == 401
        assert client.get(f"/api/v1/admin{path}", headers=organizer_headers).status_code == 403


def test_search_orders_and_payments(
    client: TestClient, admin_headers: dict[str, str], paid_event_id: str
) -> None:
    paid = place_order(client, paid_event_id, "dana@example.kz", name="Dana")
    place_order(client, paid_event_id, "erlan@example.kz", name="Erlan", fail=True)

    by_email = client.get("/api/v1/admin/orders", params={"q": "dana@"}, headers=admin_headers)
    assert by_email.status_code == 200
    [order] = by_email.json()
    assert order["id"] == paid
    assert order["event_title"] == "Paid Concert"
    assert order["status"] == "paid"

    by_id = client.get("/api/v1/admin/orders", params={"q": paid}, headers=admin_headers).json()
    assert [o["id"] for o in by_id] == [paid]

    by_event = client.get(
        "/api/v1/admin/orders", params={"q": "paid concert"}, headers=admin_headers
    ).json()
    assert len(by_event) == 2

    pending = client.get(
        "/api/v1/admin/orders", params={"status": "pending"}, headers=admin_headers
    ).json()
    assert [o["customer_email"] for o in pending] == ["erlan@example.kz"]

    failed = client.get(
        "/api/v1/admin/payments", params={"status": "failed"}, headers=admin_headers
    ).json()
    assert [p["customer_email"] for p in failed] == ["erlan@example.kz"]

    succeeded = client.get(
        "/api/v1/admin/payments", params={"q": "dana@"}, headers=admin_headers
    ).json()
    assert succeeded[0]["status"] == "succeeded"
    by_tx = client.get(
        "/api/v1/admin/payments",
        params={"q": succeeded[0]["transaction_id"]},
        headers=admin_headers,
    ).json()
    assert [p["order_id"] for p in by_tx] == [paid]


def test_monitoring_counts_failures_and_refunds(
    client: TestClient, admin_headers: dict[str, str], paid_event_id: str
) -> None:
    refunded = place_order(client, paid_event_id, "refund@example.kz")
    place_order(client, paid_event_id, "failed@example.kz", fail=True)
    with core.Session(core.engine) as db:
        order = db.get(Order, UUID(refunded))
        assert order is not None
        order.status = "refunded"
        db.commit()

    res = client.get("/api/v1/admin/monitoring", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["failed_payments"] == 1
    assert data["refunded_orders"] == 1
    assert data["refunded_amount_kzt"] == 500000
    assert data["pending_orders"] == 1
    assert [p["customer_email"] for p in data["recent_failed_payments"]] == ["failed@example.kz"]
    assert [o["id"] for o in data["recent_refunds"]] == [refunded]


def test_export_reports(
    client: TestClient, admin_headers: dict[str, str], paid_event_id: str
) -> None:
    place_order(client, paid_event_id, "csv@example.kz", name="=HYPERLINK(1)")

    res = client.get(
        "/api/v1/admin/reports/export", params={"report": "orders"}, headers=admin_headers
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    rows = list(csv.DictReader(StringIO(res.text)))
    assert [row["customer_email"] for row in rows] == ["csv@example.kz"]
    assert rows[0]["customer_name"] == "'=HYPERLINK(1)"
    assert rows[0]["status"] == "paid"

    for report in ("payments", "events", "users"):
        res = client.get(
            "/api/v1/admin/reports/export", params={"report": report}, headers=admin_headers
        )
        assert res.status_code == 200
        assert len(list(csv.DictReader(StringIO(res.text)))) >= 1

    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    empty = client.get(
        "/api/v1/admin/reports/export",
        params={"report": "orders", "date_from": future},
        headers=admin_headers,
    )
    assert list(csv.DictReader(StringIO(empty.text))) == []

    bad = client.get(
        "/api/v1/admin/reports/export", params={"report": "secrets"}, headers=admin_headers
    )
    assert bad.status_code == 422
