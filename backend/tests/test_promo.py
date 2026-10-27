from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

import core
from features.audit_log.models import AuditLog
from features.auth.service import auth_service
from features.promo.models import PromoCampaign, PromoRedemption
from features.promo.service import CODE_ALPHABET, CODE_LENGTH, QR_CAPTION, promo_service


def organizer_auth(client: TestClient) -> dict[str, str]:
    credentials = {"email": "promo-organizer@example.com", "password": "s3cretpass"}
    registered = client.post(
        "/api/v1/auth/register",
        json={**credentials, "full_name": "Promo Organizer", "role": "organizer"},
    )
    if registered.status_code == 201:
        verify_token = auth_service.create_verify_token(SimpleNamespace(id=registered.json()["id"]))
        client.post("/api/v1/auth/verify-email", json={"token": verify_token})
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_event(client: TestClient) -> str:
    headers = organizer_auth(client)
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


def create_campaign(client: TestClient, event_id: str, **overrides) -> dict:
    payload = {"name": "Instagram", "discount_type": "percent", "discount_value": 20}
    res = client.post(f"/api/v1/promo/campaigns?event_id={event_id}", json=payload | overrides)
    assert res.status_code == 201
    return res.json()


def audit_actions(entity_id: str) -> list[str]:
    with core.Session(core.engine) as db:
        stmt = (
            select(AuditLog.action)
            .where(AuditLog.entity_id == UUID(entity_id))
            .order_by(AuditLog.created_at)
        )
        return list(db.scalars(stmt).all())


def qr_token(campaign_id: str) -> str:
    with core.Session(core.engine) as db:
        campaign = db.get(PromoCampaign, UUID(campaign_id))
        assert campaign
        return campaign.qr_token


def test_create_campaign(client: TestClient) -> None:
    event_id = create_event(client)
    data = create_campaign(client, event_id)

    assert data["event_id"] == event_id
    assert data["redemption_count"] == 0
    assert data["is_disabled"] is False
    assert len(data["code"]) == CODE_LENGTH
    assert set(data["code"]) <= set(CODE_ALPHABET)
    assert "qr_token" not in data
    assert audit_actions(data["id"]) == ["promo_created"]


def test_codes_are_unique_per_campaign(client: TestClient) -> None:
    event_id = create_event(client)
    first = create_campaign(client, event_id)
    second = create_campaign(client, event_id)
    assert first["code"] != second["code"]


def test_create_campaign_for_missing_event(client: TestClient) -> None:
    res = client.post(
        f"/api/v1/promo/campaigns?event_id={uuid4()}",
        json={"name": "Instagram", "discount_type": "fixed", "discount_value": 100000},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Event not found"


def test_create_campaign_for_cancelled_event(client: TestClient) -> None:
    event_id = create_event(client)
    client.post(f"/api/v1/events/cancel?event_id={event_id}", headers=organizer_auth(client))

    res = client.post(
        f"/api/v1/promo/campaigns?event_id={event_id}",
        json={"name": "Instagram", "discount_type": "percent", "discount_value": 10},
    )
    assert res.status_code == 400


def test_create_campaign_rejects_bad_values(client: TestClient) -> None:
    event_id = create_event(client)
    url = f"/api/v1/promo/campaigns?event_id={event_id}"
    now = datetime.now(UTC)

    over_100 = {"name": "x", "discount_type": "percent", "discount_value": 150}
    assert client.post(url, json=over_100).status_code == 422

    zero = {"name": "x", "discount_type": "fixed", "discount_value": 0}
    assert client.post(url, json=zero).status_code == 422

    unknown_type = {"name": "x", "discount_type": "bogo", "discount_value": 10}
    assert client.post(url, json=unknown_type).status_code == 422

    reversed_dates = {
        "name": "x",
        "discount_type": "percent",
        "discount_value": 10,
        "start_time": (now + timedelta(days=2)).isoformat(),
        "end_time": (now + timedelta(days=1)).isoformat(),
    }
    assert client.post(url, json=reversed_dates).status_code == 422

    naive_date = {
        "name": "x",
        "discount_type": "percent",
        "discount_value": 10,
        "start_time": "2026-11-01T10:00:00",
    }
    assert client.post(url, json=naive_date).status_code == 422


def test_list_campaigns_by_event(client: TestClient) -> None:
    event_id = create_event(client)
    other_event_id = create_event(client)
    create_campaign(client, event_id, name="Instagram")
    create_campaign(client, event_id, name="Telegram")
    create_campaign(client, other_event_id, name="Posters")

    res = client.get(f"/api/v1/promo/campaigns?event_id={event_id}")
    assert res.status_code == 200
    assert sorted(c["name"] for c in res.json()) == ["Instagram", "Telegram"]


def test_get_campaign_detail(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client))

    res = client.get(f"/api/v1/promo/campaigns/detail?campaign_id={campaign['id']}")
    assert res.status_code == 200
    assert res.json()["code"] == campaign["code"]

    missing = client.get(f"/api/v1/promo/campaigns/detail?campaign_id={uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Campaign not found"


def test_update_campaign(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client))

    res = client.patch(
        f"/api/v1/promo/campaigns/update?campaign_id={campaign['id']}",
        json={"name": "Instagram stories", "max_redemptions": 50},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Instagram stories"
    assert res.json()["max_redemptions"] == 50
    assert res.json()["code"] == campaign["code"]


def test_update_campaign_checks_dates_against_stored_values(client: TestClient) -> None:
    now = datetime.now(UTC)
    campaign = create_campaign(
        client,
        create_event(client),
        start_time=(now + timedelta(days=2)).isoformat(),
    )

    res = client.patch(
        f"/api/v1/promo/campaigns/update?campaign_id={campaign['id']}",
        json={"end_time": (now + timedelta(days=1)).isoformat()},
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "end_time must be after start_time"


def test_disable_campaign(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client))
    url = f"/api/v1/promo/campaigns/disable?campaign_id={campaign['id']}"

    res = client.post(url)
    assert res.status_code == 200
    assert res.json()["is_disabled"] is True
    assert audit_actions(campaign["id"]) == ["promo_created", "promo_disabled"]

    again = client.post(url)
    assert again.status_code == 400
    assert again.json()["detail"] == "Campaign is disabled"

    update = client.patch(
        f"/api/v1/promo/campaigns/update?campaign_id={campaign['id']}", json={"name": "x"}
    )
    assert update.status_code == 400


def test_campaign_qr_is_marked_as_not_a_ticket(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client))

    res = client.get(f"/api/v1/promo/campaigns/qr?campaign_id={campaign['id']}")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert QR_CAPTION in res.text


def test_campaign_link_carries_only_the_token(client: TestClient) -> None:
    event_id = create_event(client)
    campaign = create_campaign(client, event_id, discount_value=50)

    with core.Session(core.engine) as db:
        stored = db.get(PromoCampaign, UUID(campaign["id"]))
        assert stored
        link = promo_service.campaign_link(stored)

    url = urlsplit(link)
    assert url.path == "/events/detail"
    assert parse_qs(url.query) == {"event_id": [event_id], "promo": [stored.qr_token]}


def test_resolve_promo_link(client: TestClient) -> None:
    event_id = create_event(client)
    campaign = create_campaign(client, event_id)

    res = client.get(f"/api/v1/promo/resolve?token={qr_token(campaign['id'])}")
    assert res.status_code == 200
    assert res.json()["event_id"] == event_id
    assert res.json()["code"] == campaign["code"]
    assert res.json()["discount_value"] == 20


def test_resolve_rejects_unusable_links(client: TestClient) -> None:
    event_id = create_event(client)
    now = datetime.now(UTC)

    unknown = client.get("/api/v1/promo/resolve?token=nope")
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Promo link is not valid"

    disabled = create_campaign(client, event_id)
    client.post(f"/api/v1/promo/campaigns/disable?campaign_id={disabled['id']}")
    res = client.get(f"/api/v1/promo/resolve?token={qr_token(disabled['id'])}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Promo code is disabled"

    expired = create_campaign(
        client,
        event_id,
        start_time=(now - timedelta(days=2)).isoformat(),
        end_time=(now - timedelta(days=1)).isoformat(),
    )
    res = client.get(f"/api/v1/promo/resolve?token={qr_token(expired['id'])}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Promo code has expired"

    upcoming = create_campaign(client, event_id, start_time=(now + timedelta(days=1)).isoformat())
    res = client.get(f"/api/v1/promo/resolve?token={qr_token(upcoming['id'])}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Promo code is not active yet"


def test_find_by_code(client: TestClient) -> None:
    event_id = create_event(client)
    campaign = create_campaign(client, event_id)

    with core.Session(core.engine) as db:
        found = promo_service.find_by_code(db, UUID(event_id), f" {campaign['code'].lower()} ")
        assert found and str(found.id) == campaign["id"]
        assert promo_service.find_by_code(db, uuid4(), campaign["code"]) is None


def test_calculate_discount() -> None:
    percent = PromoCampaign(discount_type="percent", discount_value=15)
    assert promo_service.calculate_discount(percent, 333_333) == 49_999

    fixed = PromoCampaign(discount_type="fixed", discount_value=500_000)
    assert promo_service.calculate_discount(fixed, 1_200_000) == 500_000
    assert promo_service.calculate_discount(fixed, 300_000) == 300_000


def test_redeem_stops_at_limit(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client), max_redemptions=1)

    with core.Session(core.engine) as db:
        stored = db.get(PromoCampaign, UUID(campaign["id"]))
        assert stored

        first = promo_service.redeem(db, stored, order_id=uuid4(), discount_amount=1000)
        db.commit()
        assert first is not None

        db.refresh(stored)
        assert stored.redemption_count == 1
        assert promo_service.redeem(db, stored, order_id=uuid4(), discount_amount=1000) is None

        redemptions = db.scalars(
            select(PromoRedemption).where(PromoRedemption.campaign_id == stored.id)
        ).all()
        assert len(redemptions) == 1

    res = client.get(f"/api/v1/promo/resolve?token={qr_token(campaign['id'])}")
    assert res.json()["detail"] == "Promo code has reached its redemption limit"


def test_redeem_checks_limit_in_the_update(client: TestClient) -> None:
    campaign = create_campaign(client, create_event(client), max_redemptions=1)

    with core.Session(core.engine) as first_db, core.Session(core.engine) as second_db:
        first = first_db.get(PromoCampaign, UUID(campaign["id"]))
        second = second_db.get(PromoCampaign, UUID(campaign["id"]))
        assert first and second

        assert (
            promo_service.redeem(first_db, first, order_id=uuid4(), discount_amount=1) is not None
        )
        first_db.commit()

        assert second.redemption_count == 0
        assert promo_service.redeem(second_db, second, order_id=uuid4(), discount_amount=1) is None
