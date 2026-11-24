from conftest import create_paid_event, place_order
from fastapi.testclient import TestClient


def timeline(client: TestClient, headers: dict[str, str], event_id: str) -> list[dict]:
    res = client.get(f"/api/v1/audit-log/timeline?event_id={event_id}", headers=headers)
    assert res.status_code == 200
    return res.json()


def test_payment_attempts_are_audited(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    paid_event_id: str,
) -> None:
    order = place_order(client, attendee_headers, paid_event_id).json()
    for simulate_failure in (True, False):
        res = client.post(
            "/api/v1/payments/simulate",
            headers=attendee_headers,
            json={"order_id": order["id"], "simulate_failure": simulate_failure},
        )
        assert res.status_code == 200

    entries = timeline(client, organizer_headers, paid_event_id)
    actions = [e["action"] for e in entries]
    assert "payment_failed" in actions
    assert "payment_succeeded" in actions
    succeeded = next(e for e in entries if e["action"] == "payment_succeeded")
    assert order["id"] in succeeded["description"]


def test_support_status_and_assignment_reach_the_timeline(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers, price=0)
    place_order(client, attendee_headers, event_id)
    case = client.post(
        "/api/v1/support/cases",
        headers=attendee_headers,
        json={
            "target": "organizer",
            "event_id": event_id,
            "category": "check_in",
            "subject": "Gate question",
            "message": "Which gate do I use?",
        },
    ).json()

    params = f"case_id={case['id']}"
    assert client.post(
        f"/api/v1/support/cases/assign?{params}", headers=organizer_headers
    ).is_success
    assert client.patch(
        f"/api/v1/support/cases/status?{params}",
        json={"status": "resolved"},
        headers=organizer_headers,
    ).is_success

    entries = timeline(client, organizer_headers, event_id)
    actions = [e["action"] for e in entries]
    assert "support_assigned" in actions
    status_entry = next(e for e in entries if e["action"] == "support_status_changed")
    assert "open -> resolved" in status_entry["description"]
