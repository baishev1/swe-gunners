from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def create_event(
    client: TestClient, headers: dict[str, str], title: str, start: timedelta, hours: int = 2
) -> str:
    venue = client.post(
        "/api/v1/venues", json={"name": "Palace", "address": "Astana"}, headers=headers
    )
    begins = datetime.now(UTC) + start
    res = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": title,
            "category": "Music",
            "venue_id": venue.json()["id"],
            "start_time": begins.isoformat(),
            "end_time": (begins + timedelta(hours=hours)).isoformat(),
            "capacity": 50,
        },
    )
    assert res.status_code == 201, res.json()
    return res.json()["id"]


def titles(events: list[dict]) -> list[str]:
    return [event["title"] for event in events]


def test_dashboard_classifies_events(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
) -> None:
    create_event(client, organizer_headers, "Upcoming", timedelta(days=3))
    create_event(client, organizer_headers, "Active", timedelta(hours=-1))
    create_event(client, organizer_headers, "Old", timedelta(days=-30))
    create_event(client, organizer_headers, "Recent", timedelta(days=-2))
    cancelled = create_event(client, organizer_headers, "Cancelled", timedelta(days=5))
    client.post(f"/api/v1/events/cancel?event_id={cancelled}", headers=organizer_headers)
    create_event(client, other_organizer_headers, "Not mine", timedelta(days=3))

    res = client.get("/api/v1/events/dashboard", headers=organizer_headers)
    assert res.status_code == 200
    data = res.json()
    assert titles(data["upcoming"]) == ["Upcoming"]
    assert titles(data["active"]) == ["Active"]
    assert titles(data["completed"]) == ["Recent", "Old"]
    assert titles(data["cancelled"]) == ["Cancelled"]


def test_dashboard_requires_organizer(client: TestClient, attendee_headers: dict[str, str]) -> None:
    assert client.get("/api/v1/events/dashboard").status_code == 401
    assert client.get("/api/v1/events/dashboard", headers=attendee_headers).status_code == 403


def test_status_changes_and_ticket_edits_reach_the_timeline(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers, "Jazz Night", timedelta(days=7))
    ticket_type = client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "VIP", "price": 0, "quantity": 10},
        headers=organizer_headers,
    ).json()
    client.patch(
        f"/api/v1/ticket-types/update?ticket_type_id={ticket_type['id']}",
        json={"quantity": 20},
        headers=organizer_headers,
    )
    client.patch(
        f"/api/v1/events/update?event_id={event_id}",
        json={"capacity": 80},
        headers=organizer_headers,
    )
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=organizer_headers)
    duplicate = client.post(
        f"/api/v1/events/duplicate?event_id={event_id}", headers=organizer_headers
    )
    assert duplicate.status_code == 201
    client.post(f"/api/v1/events/cancel?event_id={event_id}", headers=organizer_headers)

    timeline = client.get(
        "/api/v1/audit-log/timeline", params={"event_id": event_id}, headers=organizer_headers
    ).json()
    assert [entry["action"] for entry in timeline] == [
        "ticket_type_created",
        "ticket_capacity_changed",
        "event_capacity_changed",
        "event_published",
        "event_duplicated",
        "event_cancelled",
    ]
    assert all(entry["actor_name"] == "Test User" for entry in timeline)
    assert "from 10 to 20" in timeline[1]["description"]

    copy_timeline = client.get(
        "/api/v1/audit-log/timeline",
        params={"event_id": duplicate.json()["id"]},
        headers=organizer_headers,
    ).json()
    assert [entry["action"] for entry in copy_timeline] == ["event_created"]
