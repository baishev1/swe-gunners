import smtplib
from datetime import timedelta
from email.message import EmailMessage

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

import core
from core import settings
from features.auth.service import auth_service, hasher
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


def test_refresh_returns_working_tokens(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json=USER)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": USER["email"], "password": USER["password"]}
    ).json()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    access_token = response.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200


def test_refresh_rejects_access_and_expired_tokens(client: TestClient) -> None:
    access_token = login(client)
    expired = jwt.encode(
        {
            "sub": str(get_user().id),
            "purpose": "refresh",
            "exp": core.time_now() - timedelta(minutes=1),
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    for token in (access_token, expired):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401


def test_refresh_token_is_not_an_access_token(client: TestClient) -> None:
    login(client)
    refresh_token = auth_service.create_refresh_token(get_user())

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})

    assert response.status_code == 401


def test_refresh_rejects_disabled_user(client: TestClient) -> None:
    login(client)
    user = get_user()
    refresh_token = auth_service.create_refresh_token(user)
    assert core.engine is not None
    with Session(core.engine) as db:
        persisted = db.get(User, user.id)
        assert persisted is not None
        persisted.is_active = False
        db.commit()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

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


def test_verification_email_is_sent_over_smtp(client: TestClient, monkeypatch) -> None:
    sent: list[EmailMessage] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            pass

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def send_message(self, message: EmailMessage) -> None:
            sent.append(message)

    monkeypatch.setattr(settings, "SMTP_HOST", "localhost")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    client.post("/api/v1/auth/register", json=USER)

    assert len(sent) == 1
    assert sent[0]["To"] == USER["email"]
    assert "/verify-email?token=" in sent[0].get_content()


def test_smtp_logs_in_over_starttls_when_user_is_set(client: TestClient, monkeypatch) -> None:
    calls: list[str] = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float) -> None:
            calls.append(f"connect {host}:{port} timeout={timeout}")

        def __enter__(self) -> "FakeSMTP":
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def starttls(self) -> None:
            calls.append("starttls")

        def login(self, user: str, password: str) -> None:
            calls.append(f"login {user}")

        def send_message(self, message: EmailMessage) -> None:
            calls.append("send")

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "mailer@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)

    client.post("/api/v1/auth/register", json=USER)

    assert calls == [
        "connect smtp.example.com:587 timeout=10",
        "starttls",
        "login mailer@example.com",
        "send",
    ]


def test_email_is_case_insensitive(client: TestClient) -> None:
    user = {**USER, "email": "Ann.Case@Example.com"}

    registered = client.post("/api/v1/auth/register", json=user)
    assert registered.json()["email"] == "ann.case@example.com"

    login = client.post(
        "/api/v1/auth/login", json={"email": "ANN.CASE@example.com", "password": USER["password"]}
    )
    assert login.status_code == 200

    duplicate = client.post("/api/v1/auth/register", json={**user, "email": "ann.case@EXAMPLE.com"})
    assert duplicate.status_code == 409


def test_mixed_case_email_stored_earlier_still_matches(client: TestClient, monkeypatch) -> None:
    with Session(core.engine) as db:
        db.add(
            User(
                email="Old.User@Example.com",
                password_hash=hasher.hash(USER["password"]),
                full_name="Old User",
                role="attendee",
            )
        )
        db.commit()
    reset_for: list[str] = []
    monkeypatch.setattr(
        auth_service, "send_password_reset_email", lambda user: reset_for.append(user.email)
    )

    login = client.post(
        "/api/v1/auth/login", json={"email": "old.user@example.com", "password": USER["password"]}
    )
    assert login.status_code == 200

    client.post("/api/v1/auth/forgot-password", json={"email": "old.user@example.com"})
    assert reset_for == ["Old.User@Example.com"]
