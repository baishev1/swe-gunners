from fastapi.testclient import TestClient

ORGANIZER = {
    "email": "org@example.com",
    "password": "s3cretpass",
    "full_name": "Olga",
    "role": "organizer",
}
ATTENDEE = {"email": "ann@example.com", "password": "s3cretpass", "full_name": "Ann"}


def auth_headers(client: TestClient, user: dict[str, str]) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=user)
    response = client.post(
        "/api/v1/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_organizer_registration_creates_empty_profile(client: TestClient) -> None:
    headers = auth_headers(client, ORGANIZER)

    response = client.get("/api/v1/organizers/profile", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "organization_name": None,
        "contact_email": None,
        "contact_phone": None,
        "payout_recipient_name": None,
        "payout_iban": None,
        "payout_bin": None,
    }


def test_attendee_cannot_read_profile(client: TestClient) -> None:
    headers = auth_headers(client, ATTENDEE)

    response = client.get("/api/v1/organizers/profile", headers=headers)

    assert response.status_code == 403


def test_patch_updates_only_sent_fields(client: TestClient) -> None:
    headers = auth_headers(client, ORGANIZER)

    client.patch("/api/v1/organizers/profile", json={"organization_name": "Acme"}, headers=headers)
    response = client.patch(
        "/api/v1/organizers/profile", json={"contact_phone": "+77001234567"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["organization_name"] == "Acme"
    assert body["contact_phone"] == "+77001234567"


def test_patch_saves_payout_details(client: TestClient) -> None:
    headers = auth_headers(client, ORGANIZER)
    payout = {
        "payout_recipient_name": "Acme LLP",
        "payout_iban": "KZ86125KZT5004100100",
        "payout_bin": "123456789012",
    }

    client.patch("/api/v1/organizers/profile", json=payout, headers=headers)
    response = client.get("/api/v1/organizers/profile", headers=headers)

    assert response.status_code == 200
    assert response.json() | payout == response.json()
