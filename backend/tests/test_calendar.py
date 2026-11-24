from fastapi.testclient import TestClient
from test_events import create_venue, sample_event_payload


def create_published_event(client: TestClient, headers: dict[str, str], **overrides) -> str:
    payload = {**sample_event_payload(create_venue(client, headers)), **overrides}
    event_id = client.post("/api/v1/events", json=payload, headers=headers).json()["id"]
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=headers)
    return event_id


def test_calendar_file_has_event_details(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_published_event(client, organizer_headers)

    res = client.get(f"/api/v1/events/calendar?event_id={event_id}")

    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/calendar")
    assert all(len(line.encode()) <= 75 for line in res.text.split("\r\n"))
    body = res.text.replace("\r\n ", "")
    assert body.startswith("BEGIN:VCALENDAR\r\n")
    assert f"UID:{event_id}@biletflow" in body
    assert "SUMMARY:Almaty Tech Meetup" in body
    assert "LOCATION:Astana Hub Almaty\\, Al-Farabi 17" in body
    assert "X-WR-TIMEZONE:Asia/Almaty" in body
    assert f"/events/detail?event_id={event_id}" in body
    assert "STATUS:CONFIRMED" in body


def test_cancelled_event_calendar_replaces_the_entry(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_published_event(client, organizer_headers)
    before = client.get(f"/api/v1/events/calendar?event_id={event_id}").text

    client.post(f"/api/v1/events/cancel?event_id={event_id}", headers=organizer_headers)
    after = client.get(f"/api/v1/events/calendar?event_id={event_id}").text

    assert f"UID:{event_id}@biletflow" in after
    assert "STATUS:CANCELLED" in after
    assert "SUMMARY:Cancelled: Almaty Tech Meetup" in after
    sequence = lambda text: int(text.split("SEQUENCE:")[1].split("\r\n")[0])  # noqa: E731
    assert sequence(after) >= sequence(before)


def test_private_event_calendar_needs_the_access_link(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_published_event(client, organizer_headers, visibility="private")

    assert client.get(f"/api/v1/events/calendar?event_id={event_id}").status_code == 404
