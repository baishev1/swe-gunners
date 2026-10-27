from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

import core
from features.auth.service import auth_service
from features.users.models import User

USER = {"email": "ann@example.com", "password": "s3cretpass", "full_name": "Ann"}


def login(client: TestClient) -> str:
    client.post("/api/v1/auth/register", json=USER)
    response = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": USER["password"]}
    )
    return response.json()["access_token"]


def get_user() -> User:
    assert core.engine is not None
    with Session(core.engine) as db:
        return db.scalars(select(User)).one()


def test_register_returns_user_without_password(client: TestClient) -> None:
    response = client.post("/api/v1/auth/register", json=USER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER["email"]
    assert body["role"] == "attendee"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=USER)

    response = client.post("/api/v1/auth/register", json=USER)

    assert response.status_code == 409


def test_login_wrong_password_unauthorized(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=USER)

    response = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    token = login(client)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == USER["email"]


def test_me_without_or_with_bad_token_unauthorized(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_verify_email_marks_user_verified(client: TestClient) -> None:
    token = login(client)
    verify_token = auth_service.create_verify_token(get_user())

    response = client.post("/api/v1/auth/verify-email", json={"token": verify_token})
    assert response.status_code == 200
    assert response.json()["is_email_verified"] is True

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["is_email_verified"] is True


def test_verify_email_garbage_token_rejected(client: TestClient) -> None:
    login(client)

    response = client.post("/api/v1/auth/verify-email", json={"token": "garbage"})

    assert response.status_code == 400


def test_verify_email_expired_token_rejected(client: TestClient) -> None:
    login(client)
    user = get_user()
    expired = jwt.encode(
        {"sub": str(user.id), "purpose": "verify", "exp": core.time_now() - timedelta(hours=1)},
        core.settings.JWT_SECRET,
        algorithm=core.settings.JWT_ALGORITHM,
    )

    response = client.post("/api/v1/auth/verify-email", json={"token": expired})

    assert response.status_code == 400


def test_verify_email_rejects_reset_token(client: TestClient) -> None:
    login(client)
    reset_token = auth_service.create_reset_token(get_user())

    response = client.post("/api/v1/auth/verify-email", json={"token": reset_token})

    assert response.status_code == 400


def test_resend_verification_requires_auth(client: TestClient) -> None:
    token = login(client)

    assert client.post("/api/v1/auth/resend-verification").status_code == 401
    response = client.post(
        "/api/v1/auth/resend-verification", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204


def test_reset_password_changes_credentials(client: TestClient) -> None:
    login(client)
    reset_token = auth_service.create_reset_token(get_user())

    response = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "brand-new-pass"}
    )
    assert response.status_code == 204

    old = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": USER["password"]}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": "brand-new-pass"}
    )
    assert new.status_code == 200


def test_reset_token_is_single_use(client: TestClient) -> None:
    login(client)
    reset_token = auth_service.create_reset_token(get_user())
    payload = {"token": reset_token, "new_password": "brand-new-pass"}
    client.post("/api/v1/auth/reset-password", json=payload)

    response = client.post("/api/v1/auth/reset-password", json=payload)

    assert response.status_code == 400


def test_forgot_password_unknown_email_returns_204(client: TestClient) -> None:
    response = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})

    assert response.status_code == 204
