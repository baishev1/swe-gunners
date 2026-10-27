from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import core
from app.main import app
from core import Session
from features.users.dependencies import get_current_user as get_support_user
from features.users.models import User


@pytest.fixture(autouse=True)
def no_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core.settings, "SMTP_HOST", "")


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        if core.engine is not None:
            core.DbBase.metadata.create_all(core.engine)
        yield test_client


def make_headers(client: TestClient, email: str, role: str) -> dict[str, str]:
    user = {"email": email, "password": "s3cretpass", "full_name": "Test User", "role": role}
    client.post("/api/v1/auth/register", json=user)
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": user["password"]}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def organizer_headers(client: TestClient) -> dict[str, str]:
    return make_headers(client, "org@example.com", "organizer")


@pytest.fixture
def other_organizer_headers(client: TestClient) -> dict[str, str]:
    return make_headers(client, "other@example.com", "organizer")


@pytest.fixture
def attendee_headers(client: TestClient) -> dict[str, str]:
    return make_headers(client, "ann@example.com", "attendee")


@pytest.fixture
def login(client: TestClient) -> Iterator[Callable[[str], User]]:
    users: dict[str, User] = {}
    assert core.engine is not None
    with Session(core.engine) as db:
        for name, role in (
            ("attendee", "attendee"),
            ("other", "attendee"),
            ("organizer", "organizer"),
            ("other_organizer", "organizer"),
            ("admin", "platform_admin"),
        ):
            user = User(
                email=f"{uuid4()}@example.com",
                full_name=name,
                password_hash="unused-in-tests",
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            db.expunge(user)
            users[name] = user

    def switch(name: str) -> User:
        user = users[name]
        app.dependency_overrides[get_support_user] = lambda: user
        return user

    switch("attendee")
    try:
        yield switch
    finally:
        app.dependency_overrides.pop(get_support_user, None)
