from conftest import make_headers, place_order
from fastapi.testclient import TestClient


def paid_tickets(
    client: TestClient, headers: dict[str, str], event_id: str, quantity: int
) -> list[dict]:
    order = place_order(client, headers, event_id, quantity=quantity).json()
    client.post(
        "/api/v1/payments/simulate",
        headers=headers,
        json={"order_id": order["id"], "simulate_failure": False},
    )
    return client.get(f"/api/v1/tickets?order_id={order['id']}", headers=headers).json()


def assign(
    client: TestClient,
    owner_headers: dict[str, str],
    event_id: str,
    can_undo: bool = False,
) -> dict[str, str]:
    staff_headers = make_headers(client, "door@example.com", "attendee")
    staff_id = client.get("/api/v1/auth/me", headers=staff_headers).json()["id"]
    res = client.post(
        f"/api/v1/checkin/staff?event_id={event_id}",
        json={"user_id": staff_id, "can_undo_check_in": can_undo},
        headers=owner_headers,
    )
    assert res.status_code == 201, res.json()
    return staff_headers


def test_assigned_events_report_undo_permission(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    staff_headers = assign(client, organizer_headers, paid_event_id)

    staff_events = client.get("/api/v1/checkin/events", headers=staff_headers).json()
    assert [(e["id"], e["can_undo_check_in"]) for e in staff_events] == [(paid_event_id, False)]

    owner_events = client.get("/api/v1/checkin/events", headers=organizer_headers).json()
    assert [e["can_undo_check_in"] for e in owner_events] == [True]


def test_staff_sees_summary_after_check_in(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    tickets = paid_tickets(client, attendee_headers, paid_event_id, quantity=3)
    place_order(client, attendee_headers, paid_event_id)
    staff_headers = assign(client, organizer_headers, paid_event_id)
    params = {"event_id": paid_event_id}

    client.post(
        "/api/v1/tickets/check-in",
        params={**params, "ticket_id": tickets[0]["id"]},
        headers=staff_headers,
    )

    res = client.get("/api/v1/checkin/summary", params=params, headers=staff_headers)
    assert res.status_code == 200
    assert res.json() == {"event_id": paid_event_id, "registered": 3, "checked_in": 1}


def test_staff_searches_attendees(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    tickets = paid_tickets(client, attendee_headers, paid_event_id, quantity=2)
    staff_headers = assign(client, organizer_headers, paid_event_id)
    url = f"/api/v1/checkin/attendees?event_id={paid_event_id}"

    assert len(client.get(url, headers=staff_headers).json()) == 2
    by_email = client.get(f"{url}&q=ARMAN@", headers=staff_headers).json()
    assert len(by_email) == 2
    by_id = client.get(f"{url}&q={tickets[0]['id']}", headers=staff_headers).json()
    assert [a["ticket_id"] for a in by_id] == [tickets[0]["id"]]
    assert client.get(f"{url}&q=nobody", headers=staff_headers).json() == []


def test_unassigned_user_cannot_read_attendees_or_summary(
    client: TestClient, attendee_headers: dict[str, str], paid_event_id: str
) -> None:
    params = {"event_id": paid_event_id}

    assert (
        client.get("/api/v1/checkin/attendees", params=params, headers=attendee_headers).status_code
        == 404
    )
    assert (
        client.get("/api/v1/checkin/summary", params=params, headers=attendee_headers).status_code
        == 404
    )
