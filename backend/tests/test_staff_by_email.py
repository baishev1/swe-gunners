from conftest import make_headers
from fastapi.testclient import TestClient


def staff_url(event_id: str) -> str:
    return f"/api/v1/checkin/staff?event_id={event_id}"


def test_organizer_assigns_staff_by_email(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    staff_headers = make_headers(client, "door.keeper@example.com", "attendee")

    # Emails are matched case-insensitively, as at sign-in.
    res = client.post(
        staff_url(paid_event_id),
        json={"email": "  Door.Keeper@Example.com ", "can_undo_check_in": True},
        headers=organizer_headers,
    )

    assert res.status_code == 201
    body = res.json()
    assert body["user_email"] == "door.keeper@example.com"
    assert body["user_full_name"] == "Test User"
    assert body["can_undo_check_in"] is True

    listed = client.get(staff_url(paid_event_id), headers=organizer_headers).json()
    assert [s["user_email"] for s in listed] == ["door.keeper@example.com"]
    # The assigned person now sees the event in the mobile app.
    events = client.get("/api/v1/checkin/events", headers=staff_headers).json()
    assert [e["id"] for e in events] == [paid_event_id]


def test_staff_changes_are_in_the_event_timeline(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    make_headers(client, "gate@example.com", "attendee")
    assignment = client.post(
        staff_url(paid_event_id), json={"email": "gate@example.com"}, headers=organizer_headers
    ).json()
    removed = client.delete(
        f"{staff_url(paid_event_id)}&assignment_id={assignment['id']}", headers=organizer_headers
    )
    assert removed.status_code == 204

    timeline = client.get(
        f"/api/v1/audit-log/timeline?event_id={paid_event_id}", headers=organizer_headers
    ).json()
    actions = [entry["action"] for entry in timeline]
    assert "staff_assigned" in actions
    assert "staff_removed" in actions


def test_unknown_email_and_bad_payloads_are_rejected(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    unknown = client.post(
        staff_url(paid_event_id), json={"email": "nobody@example.com"}, headers=organizer_headers
    )
    assert unknown.status_code == 404

    neither = client.post(staff_url(paid_event_id), json={}, headers=organizer_headers)
    assert neither.status_code == 422

    owner_id = client.get("/api/v1/auth/me", headers=organizer_headers).json()["id"]
    both = client.post(
        staff_url(paid_event_id),
        json={"email": "x@example.com", "user_id": owner_id},
        headers=organizer_headers,
    )
    assert both.status_code == 422


def test_duplicate_assignment_is_rejected(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    make_headers(client, "twice@example.com", "attendee")
    first = client.post(
        staff_url(paid_event_id), json={"email": "twice@example.com"}, headers=organizer_headers
    )
    second = client.post(
        staff_url(paid_event_id), json={"email": "twice@example.com"}, headers=organizer_headers
    )

    assert first.status_code == 201
    assert second.status_code == 409
