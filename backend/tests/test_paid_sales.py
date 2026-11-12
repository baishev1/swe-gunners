from collections.abc import Callable

from conftest import place_order
from fastapi.testclient import TestClient


def checklist(client: TestClient, headers: dict[str, str], event_id: str) -> dict:
    response = client.get(f"/api/v1/paid-sales/checklist?event_id={event_id}", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_new_event_starts_with_empty_checklist(
    client: TestClient, organizer_headers: dict[str, str], make_paid_event: Callable[..., str]
) -> None:
    event_id = make_paid_event()

    data = checklist(client, organizer_headers, event_id)

    assert data["status"] == "pending"
    assert data["has_paid_ticket_type"] is True
    assert data["identity_verified"] is False
    assert data["payout_account_ready"] is False
    assert data["fee_paid"] is False
    assert data["terms_accepted"] is False
    assert data["can_activate"] is False


def test_full_activation_flow_records_fee_and_audit_trail(
    client: TestClient,
    organizer_headers: dict[str, str],
    make_paid_event: Callable[..., str],
    complete_checklist: Callable[[str], None],
    admin_headers: dict[str, str],
) -> None:
    client.patch("/api/v1/admin/settings", json={"activation_fee": 1500000}, headers=admin_headers)
    event_id = make_paid_event()

    complete_checklist(event_id)
    ready = checklist(client, organizer_headers, event_id)
    assert ready["can_activate"] is True
    assert ready["fee_amount"] == 1500000
    assert ready["fee_transaction_id"].startswith("sim_")

    response = client.post(
        f"/api/v1/paid-sales/activate?event_id={event_id}", headers=organizer_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["activated_at"] is not None

    timeline = client.get(
        f"/api/v1/audit-log/timeline?event_id={event_id}", headers=organizer_headers
    ).json()
    actions = [entry["action"] for entry in timeline]
    assert "activation_fee_paid" in actions
    assert "paid_terms_accepted" in actions
    assert "paid_sales_activated" in actions


def test_activation_lists_missing_steps(
    client: TestClient, organizer_headers: dict[str, str], make_paid_event: Callable[..., str]
) -> None:
    event_id = make_paid_event()
    client.post(f"/api/v1/paid-sales/accept-terms?event_id={event_id}", headers=organizer_headers)

    response = client.post(
        f"/api/v1/paid-sales/activate?event_id={event_id}", headers=organizer_headers
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "identity verification" in detail
    assert "a payout account" in detail
    assert "the activation fee" in detail
    assert "accepted paid-event terms" not in detail


def test_activation_requires_a_paid_ticket_type(
    client: TestClient,
    organizer_headers: dict[str, str],
    make_paid_event: Callable[..., str],
    complete_checklist: Callable[[str], None],
) -> None:
    event_id = make_paid_event(price=0)
    complete_checklist(event_id)

    response = client.post(
        f"/api/v1/paid-sales/activate?event_id={event_id}", headers=organizer_headers
    )

    assert response.status_code == 400
    assert "a paid ticket type" in response.json()["detail"]


def test_failed_fee_payment_is_not_recorded(
    client: TestClient, organizer_headers: dict[str, str], make_paid_event: Callable[..., str]
) -> None:
    event_id = make_paid_event()

    response = client.post(
        f"/api/v1/paid-sales/pay-fee?event_id={event_id}",
        json={"simulate_failure": True},
        headers=organizer_headers,
    )

    assert response.status_code == 402
    assert checklist(client, organizer_headers, event_id)["fee_paid"] is False


def test_checklist_is_private_to_the_event_owner(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    make_paid_event: Callable[..., str],
) -> None:
    event_id = make_paid_event()
    url = f"/api/v1/paid-sales/checklist?event_id={event_id}"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=attendee_headers).status_code == 403
    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert (
        client.post(
            f"/api/v1/paid-sales/accept-terms?event_id={event_id}",
            headers=other_organizer_headers,
        ).status_code
        == 404
    )


def test_activation_applies_only_to_the_selected_event(
    client: TestClient,
    organizer_headers: dict[str, str],
    paid_event_id: str,
    make_paid_event: Callable[..., str],
    attendee_headers: dict[str, str],
) -> None:
    other_event_id = make_paid_event()

    assert checklist(client, organizer_headers, paid_event_id)["status"] == "active"
    assert checklist(client, organizer_headers, other_event_id)["status"] == "pending"
    response = place_order(client, attendee_headers, other_event_id)
    assert response.status_code == 403


def test_paid_orders_are_blocked_until_activation(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    make_paid_event: Callable[..., str],
) -> None:
    event_id = make_paid_event()

    blocked = place_order(client, attendee_headers, event_id)
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Paid ticket sales are not active for this event"

    free_type = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Free", "price": 0, "quantity": 10},
        headers=organizer_headers,
    ).json()
    free = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Aliya Nurlanova",
            "customer_email": "aliya@example.kz",
            "items": [{"ticket_type_id": free_type["id"], "quantity": 1}],
        },
    )
    assert free.status_code == 201


def test_client_price_cannot_open_a_paid_ticket_type(
    client: TestClient, attendee_headers: dict[str, str], make_paid_event: Callable[..., str]
) -> None:
    event_id = make_paid_event()
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["id"]

    response = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Aliya Nurlanova",
            "customer_email": "aliya@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": 1, "unit_price_kzt": 0}],
        },
    )

    assert response.status_code == 403


def test_admin_suspension_stops_paid_sales_until_reinstated(
    client: TestClient,
    organizer_headers: dict[str, str],
    paid_event_id: str,
    admin_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    pending_order = place_order(client, attendee_headers, paid_event_id).json()

    records = client.get("/api/v1/admin/paid-sales?status=active", headers=admin_headers).json()
    assert [r["event_id"] for r in records] == [paid_event_id]
    assert records[0]["event_title"] == "Paid Concert"

    suspended = client.post(
        f"/api/v1/admin/paid-sales/suspend?event_id={paid_event_id}",
        json={"reason": "Chargeback pattern"},
        headers=admin_headers,
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"
    assert suspended.json()["suspension_reason"] == "Chargeback pattern"

    assert place_order(client, attendee_headers, paid_event_id).status_code == 403
    payment = client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": pending_order["id"]},
    )
    assert payment.status_code == 403
    reactivate = client.post(
        f"/api/v1/paid-sales/activate?event_id={paid_event_id}", headers=organizer_headers
    )
    assert reactivate.status_code == 403

    reinstated = client.post(
        f"/api/v1/admin/paid-sales/reinstate?event_id={paid_event_id}", headers=admin_headers
    )
    assert reinstated.json()["status"] == "active"
    assert place_order(client, attendee_headers, paid_event_id).status_code == 201


def test_suspending_the_event_stops_sales(
    client: TestClient,
    paid_event_id: str,
    admin_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    client.post(f"/api/v1/admin/events/suspend?event_id={paid_event_id}", headers=admin_headers)

    assert place_order(client, attendee_headers, paid_event_id).status_code == 400


def test_only_platform_admins_manage_paid_sales(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    assert client.get("/api/v1/admin/paid-sales", headers=organizer_headers).status_code == 403
    response = client.post(
        f"/api/v1/admin/paid-sales/suspend?event_id={paid_event_id}",
        json={"reason": "x"},
        headers=organizer_headers,
    )
    assert response.status_code == 403


def test_verify_identity_is_simulated_and_idempotent(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    first = client.post("/api/v1/organizers/verify-identity", headers=organizer_headers)
    second = client.post("/api/v1/organizers/verify-identity", headers=organizer_headers)

    assert first.status_code == 200
    assert first.json()["identity_verified_at"] is not None
    assert second.json()["identity_verified_at"] == first.json()["identity_verified_at"]
