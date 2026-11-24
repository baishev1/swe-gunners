from conftest import create_paid_event, make_headers, place_order
from fastapi.testclient import TestClient


def test_admin_reinstates_a_wrongly_suspended_user(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    victim_headers = make_headers(client, "innocent@example.com", "attendee")
    user_id = client.get("/api/v1/auth/me", headers=victim_headers).json()["id"]

    suspended = client.post(f"/api/v1/admin/users/suspend?user_id={user_id}", headers=admin_headers)
    assert suspended.json()["is_active"] is False
    assert client.get("/api/v1/auth/me", headers=victim_headers).status_code in (401, 403)

    reinstated = client.post(
        f"/api/v1/admin/users/reinstate?user_id={user_id}", headers=admin_headers
    )
    assert reinstated.status_code == 200
    assert reinstated.json()["is_active"] is True
    assert client.get("/api/v1/auth/me", headers=victim_headers).status_code == 200

    again = client.post(f"/api/v1/admin/users/reinstate?user_id={user_id}", headers=admin_headers)
    assert again.status_code == 400


def test_reinstated_event_returns_to_its_previous_status_and_sells(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    url = f"/api/v1/admin/events/{{}}?event_id={event_id}"

    assert client.post(url.format("suspend"), headers=admin_headers).json()["status"] == "suspended"
    ticket_type_id = client.get(
        f"/api/v1/ticket-types?event_id={event_id}", headers=organizer_headers
    ).json()[0]["id"]
    blocked = client.post(
        "/api/v1/orders",
        headers=attendee_headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": 1}],
        },
    )
    assert blocked.status_code == 400

    res = client.post(url.format("reinstate"), headers=admin_headers)

    assert res.status_code == 200
    assert res.json()["status"] == "published"
    assert place_order(client, attendee_headers, event_id).status_code == 201
    timeline = client.get(
        f"/api/v1/audit-log/timeline?event_id={event_id}", headers=organizer_headers
    ).json()
    assert "event_reinstated" in [e["action"] for e in timeline]


def test_only_admins_reinstate(
    client: TestClient, organizer_headers: dict[str, str], admin_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    client.post(f"/api/v1/admin/events/suspend?event_id={event_id}", headers=admin_headers)

    res = client.post(
        f"/api/v1/admin/events/reinstate?event_id={event_id}", headers=organizer_headers
    )

    assert res.status_code == 403
