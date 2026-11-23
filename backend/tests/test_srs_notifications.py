import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from conftest import place_order
from fastapi.testclient import TestClient
from test_support import open_case, support_event

from features.users.models import User


def shifted(iso: str, hours: int = 1) -> str:
    return (datetime.fromisoformat(iso) + timedelta(hours=hours)).isoformat()


def test_ticket_holders_hear_about_schedule_change(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )
    event = client.get(f"/api/v1/events/detail?event_id={paid_event_id}").json()

    with caplog.at_level(logging.INFO):
        res = client.patch(
            f"/api/v1/events/update?event_id={paid_event_id}",
            headers=organizer_headers,
            json={
                "start_time": shifted(event["start_time"]),
                "end_time": shifted(event["end_time"]),
            },
        )

    assert res.status_code == 200
    assert "Event update: Paid Concert" in caplog.text
    assert "arman@example.kz" in caplog.text


def test_cosmetic_event_edit_sends_no_update_email(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    client.post(
        "/api/v1/payments/simulate",
        headers=attendee_headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )

    with caplog.at_level(logging.INFO):
        res = client.patch(
            f"/api/v1/events/update?event_id={paid_event_id}",
            headers=organizer_headers,
            json={"description": "Now with more details"},
        )

    assert res.status_code == 200
    assert "Event update:" not in caplog.text


def test_organizer_hears_about_payout_status(
    client: TestClient,
    admin_headers: dict[str, str],
    paid_event_id: str,
    caplog,
) -> None:
    with caplog.at_level(logging.INFO):
        res = client.post(
            f"/api/v1/admin/paid-sales/suspend?event_id={paid_event_id}",
            json={"reason": "Chargeback pattern"},
            headers=admin_headers,
        )

    assert res.status_code == 200
    assert "Payout status for Paid Concert: suspended" in caplog.text
    assert "Chargeback pattern" in caplog.text


def test_support_reply_assignment_and_status_emails(
    client: TestClient, login: Callable[[str], User], caplog
) -> None:
    owner = login("organizer")
    event_id = support_event(client, owner)
    requester = login("attendee")

    with caplog.at_level(logging.INFO):
        case_id = open_case(client, event_id)
    # A new case reaches the event organizer, who handles it by default.
    assert "New reply in support case: Missing ticket" in caplog.text
    assert owner.email in caplog.text

    caplog.clear()
    login("organizer")
    params = {"case_id": case_id}
    with caplog.at_level(logging.INFO):
        assert client.post("/api/v1/support/cases/assign", params=params).status_code == 200
        client.post("/api/v1/support/messages", params=params, json={"body": "Resent it."})
        client.patch("/api/v1/support/cases/status", params=params, json={"status": "resolved"})

    assert "Support case assigned: Missing ticket" in caplog.text
    assert "New reply in support case: Missing ticket" in caplog.text
    assert "Support case status: Resolved" in caplog.text
    assert requester.email in caplog.text
