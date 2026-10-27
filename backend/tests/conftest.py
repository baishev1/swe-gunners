from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import core
from app.main import app


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
