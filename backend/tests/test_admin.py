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


def test_admin_routes_need_platform_admin(
    client: TestClient, organizer_headers: dict[str, str]
) -> None:
    assert client.get("/api/v1/admin/users").status_code == 401
    assert client.get("/api/v1/admin/users", headers=organizer_headers).status_code == 403
    assert client.get("/api/v1/admin/settings", headers=organizer_headers).status_code == 403


def test_search_users(
    client: TestClient, organizer_headers: dict[str, str], attendee_headers: dict[str, str]
) -> None:
    headers = platform_admin_headers(client)

    res = client.get("/api/v1/admin/users", params={"q": "ann@"}, headers=headers)
    assert res.status_code == 200
    assert [u["email"] for u in res.json()] == ["ann@example.com"]

    organizers = client.get("/api/v1/admin/users", params={"role": "organizer"}, headers=headers)
    assert [u["email"] for u in organizers.json()] == ["org@example.com"]


def test_suspend_user_blocks_login(client: TestClient, attendee_headers: dict[str, str]) -> None:
    headers = platform_admin_headers(client)
    user = client.get("/api/v1/admin/users", params={"q": "ann@"}, headers=headers).json()[0]

    res = client.post(f"/api/v1/admin/users/suspend?user_id={user['id']}", headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    login = client.post(
        "/api/v1/auth/login", json={"email": "ann@example.com", "password": "s3cretpass"}
    )
    assert login.status_code == 403

    again = client.post(f"/api/v1/admin/users/suspend?user_id={user['id']}", headers=headers)
    assert again.status_code == 400


def test_admin_cannot_suspend_self(client: TestClient) -> None:
    headers = platform_admin_headers(client)
    me = client.get("/api/v1/admin/users", params={"q": "staff@"}, headers=headers).json()[0]

    res = client.post(f"/api/v1/admin/users/suspend?user_id={me['id']}", headers=headers)
    assert res.status_code == 400
    assert res.json()["detail"] == "You cannot suspend your own account"


def test_suspend_event(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers)
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=organizer_headers)
    headers = platform_admin_headers(client)

    found = client.get("/api/v1/admin/events", params={"q": "tech meetup"}, headers=headers)
    assert [e["id"] for e in found.json()] == [event_id]

    res = client.post(f"/api/v1/admin/events/suspend?event_id={event_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "suspended"

    public = client.get("/api/v1/events").json()
    assert event_id not in [e["id"] for e in public]

    timeline = client.get(f"/api/v1/audit-log/timeline?event_id={event_id}", headers=headers)
    assert [e["action"] for e in timeline.json()] == ["event_suspended"]

    again = client.post(f"/api/v1/admin/events/suspend?event_id={event_id}", headers=headers)
    assert again.status_code == 400


def test_search_promo_campaigns(client: TestClient, organizer_headers: dict[str, str]) -> None:
    event_id = create_event(client, organizer_headers)
    campaign = client.post(
        f"/api/v1/promo/campaigns?event_id={event_id}",
        json={"name": "Telegram", "discount_type": "fixed", "discount_value": 100000},
        headers=organizer_headers,
    ).json()
    headers = platform_admin_headers(client)

    res = client.get(
        "/api/v1/admin/promo-campaigns", params={"q": campaign["code"]}, headers=headers
    )
    assert [c["id"] for c in res.json()] == [campaign["id"]]


def test_platform_settings(client: TestClient) -> None:
    headers = platform_admin_headers(client)

    res = client.get("/api/v1/admin/settings", headers=headers)
    assert res.status_code == 200
    assert res.json()["activation_fee"] == 0

    updated = client.patch(
        "/api/v1/admin/settings", json={"activation_fee": 1_500_000}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["activation_fee"] == 1_500_000
    assert client.get("/api/v1/admin/settings", headers=headers).json()["activation_fee"] == (
        1_500_000
    )

    negative = client.patch("/api/v1/admin/settings", json={"activation_fee": -1}, headers=headers)
    assert negative.status_code == 422
