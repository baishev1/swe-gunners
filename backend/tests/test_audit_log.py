from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

import core
from features.users.models import User


def platform_admin_headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": "staff@example.com", "password": "s3cretpass"}
    client.post(
        "/api/v1/auth/register",
        json={**credentials, "full_name": "Platform Staff", "role": "attendee"},
    )
    with core.Session(core.engine) as db:
        user = db.scalars(select(User).where(User.email == credentials["email"])).one()
        user.role = "platform_admin"
        db.commit()
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_event(client: TestClient, headers: dict[str, str]) -> str:
    venue = client.post(
        "/api/v1/venues",
        json={"name": "Astana Hub Almaty", "address": "Al-Farabi 17"},
        headers=headers,
    )
    now = datetime.now(UTC)
    res = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Almaty Tech Meetup",
            "category": "Technology",
            "venue_id": venue.json()["id"],
            "start_time": (now + timedelta(days=5)).isoformat(),
            "end_time": (now + timedelta(days=5, hours=3)).isoformat(),
            "capacity": 100,
        },
    )
    return res.json()["id"]


def create_and_disable_campaign(client: TestClient, event_id: str, headers: dict[str, str]):
    res = client.post(
        f"/api/v1/promo/campaigns?event_id={event_id}",
        json={"name": "Instagram", "discount_type": "percent", "discount_value": 20},
        headers=headers,
    )
    campaign_id = res.json()["id"]
    client.post(f"/api/v1/promo/campaigns/disable?campaign_id={campaign_id}", headers=headers)


def test_timeline_lists_event_activity_in_order(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    event_id = create_event(client, organizer_headers)
    create_and_disable_campaign(client, event_id, organizer_headers)

    res = client.get(f"/api/v1/audit-log/timeline?event_id={event_id}", headers=organizer_headers)
    assert res.status_code == 200
    entries = res.json()
    assert [e["action"] for e in entries] == ["promo_created", "promo_disabled"]
    assert entries[0]["actor_name"] == "Test User"
    assert entries[0]["entity_type"] == "promo_campaign"


def test_timeline_filters(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers)
    create_and_disable_campaign(client, event_id, organizer_headers)
    url = f"/api/v1/audit-log/timeline?event_id={event_id}"

    by_action = client.get(f"{url}&action=promo_disabled", headers=organizer_headers).json()
    assert [e["action"] for e in by_action] == ["promo_disabled"]

    tomorrow = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    later = client.get(
        "/api/v1/audit-log/timeline",
        params={"event_id": event_id, "date_from": tomorrow},
        headers=organizer_headers,
    ).json()
    assert later == []


def test_timeline_access(
    client: TestClient,
    organizer_headers: dict[str, str],
    other_organizer_headers: dict[str, str],
    attendee_headers: dict[str, str],
) -> None:
    event_id = create_event(client, organizer_headers)
    url = f"/api/v1/audit-log/timeline?event_id={event_id}"

    assert client.get(url).status_code == 401
    assert client.get(url, headers=other_organizer_headers).status_code == 404
    assert client.get(url, headers=attendee_headers).status_code == 404
    assert client.get(url, headers=platform_admin_headers(client)).status_code == 200
