from typing import Any

from fastapi.testclient import TestClient


def create_campaign(
    client: TestClient, headers: dict[str, str], event_id: str, **overrides: Any
) -> dict:
    payload = {"name": "Radio", "discount_type": "fixed", "discount_value": 100000}
    res = client.post(
        f"/api/v1/promo/campaigns?event_id={event_id}", json=payload | overrides, headers=headers
    )
    assert res.status_code == 201
    return res.json()


def validate(client: TestClient, event_id: str, code: str):
    return client.get(f"/api/v1/promo/validate?event_id={event_id}&code={code}")


def test_typed_code_is_validated_without_the_qr_token(
    client: TestClient, organizer_headers: dict[str, str], paid_event_id: str
) -> None:
    campaign = create_campaign(client, organizer_headers, paid_event_id)

    # Codes are case-insensitive and surrounding spaces do not matter.
    res = validate(client, paid_event_id, f"  {campaign['code'].lower()} ")

    assert res.status_code == 200
    assert res.json()["code"] == campaign["code"]
    assert res.json()["discount_type"] == "fixed"
    assert res.json()["discount_value"] == 100000
    assert "qr_token" not in res.json()


def test_unknown_and_disabled_codes_are_rejected(
    client: TestClient,
    organizer_headers: dict[str, str],
    paid_event_id: str,
    make_paid_event,
) -> None:
    assert validate(client, paid_event_id, "NOPE1234").status_code == 404

    campaign = create_campaign(client, organizer_headers, paid_event_id)
    # A code belongs to its own event only.
    other_event = make_paid_event()
    assert validate(client, other_event, campaign["code"]).status_code == 404

    client.post(
        f"/api/v1/promo/campaigns/disable?campaign_id={campaign['id']}", headers=organizer_headers
    )
    disabled = validate(client, paid_event_id, campaign["code"])
    assert disabled.status_code == 400
    assert "disabled" in disabled.json()["detail"]
