from conftest import create_paid_event
from fastapi.testclient import TestClient

REPORT = {"category": "fraud", "reason": "The organizer asks to pay by bank transfer."}


def test_attendee_reports_event(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers)

    res = client.post(
        f"/api/v1/event-reports?event_id={event_id}", json=REPORT, headers=attendee_headers
    )

    assert res.status_code == 201
    assert res.json()["status"] == "open"
    assert res.json()["category"] == "fraud"
    assert res.json()["event"]["id"] == event_id


def test_report_requires_sign_in(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_paid_event(client, organizer_headers)

    res = client.post(f"/api/v1/event-reports?event_id={event_id}", json=REPORT)

    assert res.status_code == 401


def test_report_rejects_unknown_category(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    event_id = create_paid_event(client, organizer_headers)

    res = client.post(
        f"/api/v1/event-reports?event_id={event_id}",
        json={"category": "spam", "reason": "x"},
        headers=attendee_headers,
    )

    assert res.status_code == 422


def test_admin_reviews_report(
    client: TestClient,
    organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    event_id = create_paid_event(client, organizer_headers)
    report_id = client.post(
        f"/api/v1/event-reports?event_id={event_id}", json=REPORT, headers=attendee_headers
    ).json()["id"]

    open_reports = client.get("/api/v1/admin/event-reports?status=open", headers=admin_headers)
    assert [r["id"] for r in open_reports.json()] == [report_id]

    res = client.post(
        f"/api/v1/admin/event-reports/review?report_id={report_id}", headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "reviewed"

    again = client.post(
        f"/api/v1/admin/event-reports/review?report_id={report_id}", headers=admin_headers
    )
    assert again.status_code == 400

    open_reports = client.get("/api/v1/admin/event-reports?status=open", headers=admin_headers)
    assert open_reports.json() == []


def test_only_admin_lists_reports(client: TestClient, organizer_headers: dict[str, str]) -> None:
    res = client.get("/api/v1/admin/event-reports", headers=organizer_headers)

    assert res.status_code == 403
