from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select

import core
from app.main import app
from core import Session
from features.auth.service import auth_service
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
                is_email_verified=True,
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


def make_headers(client: TestClient, email: str, role: str) -> dict[str, str]:
    user = {"email": email, "password": "s3cretpass", "full_name": "Test User", "role": role}
    registered = client.post("/api/v1/auth/register", json=user)
    token = auth_service.create_verify_token(User(id=UUID(registered.json()["id"])))
    client.post("/api/v1/auth/verify-email", json={"token": token})
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
def admin_headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": "admin@example.com", "password": "s3cretpass"}
    client.post(
        "/api/v1/auth/register",
        json={**credentials, "full_name": "Platform Admin", "role": "attendee"},
    )
    with core.Session(core.engine) as db:
        user = db.scalars(select(User).where(User.email == credentials["email"])).one()
        user.role = "platform_admin"
        db.commit()
    token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_paid_event(
    client: TestClient, headers: dict[str, str], price: int = 500000, quantity: int = 100
) -> str:
    """Creates a published event with one ticket type; paid sales are not activated yet."""
    venue = client.post(
        "/api/v1/venues", json={"name": "Baluan Sholak", "address": "Abai 44"}, headers=headers
    )
    now = datetime.now(UTC)
    event = client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Paid Concert",
            "category": "Music",
            "venue_id": venue.json()["id"],
            "start_time": (now + timedelta(days=10)).isoformat(),
            "end_time": (now + timedelta(days=10, hours=2)).isoformat(),
            "capacity": 200,
        },
    )
    event_id = event.json()["id"]
    client.post(
        f"/api/v1/ticket-types?event_id={event_id}",
        json={"name": "Standard", "price": price, "quantity": quantity},
        headers=headers,
    )
    client.post(f"/api/v1/events/publish?event_id={event_id}", headers=headers)
    return event_id


def place_order(
    client: TestClient, headers: dict[str, str], event_id: str, quantity: int = 1
) -> Response:
    ticket_type_id = client.get(f"/api/v1/ticket-types?event_id={event_id}").json()[0]["id"]
    return client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "event_id": event_id,
            "customer_name": "Arman Bekov",
            "customer_email": "arman@example.kz",
            "items": [{"ticket_type_id": ticket_type_id, "quantity": quantity}],
        },
    )


def complete_activation_checklist(
    client: TestClient, headers: dict[str, str], event_id: str
) -> None:
    client.patch(
        "/api/v1/organizers/profile",
        json={
            "payout_recipient_name": "Olga Events LLP",
            "payout_iban": "KZ86125KZT5004100100",
            "payout_bin": "123456789012",
        },
        headers=headers,
    )
    client.post("/api/v1/organizers/verify-identity", headers=headers)
    client.post(
        f"/api/v1/paid-sales/pay-fee?event_id={event_id}",
        json={"simulate_failure": False},
        headers=headers,
    )
    client.post(f"/api/v1/paid-sales/accept-terms?event_id={event_id}", headers=headers)


@pytest.fixture
def make_paid_event(client: TestClient, organizer_headers: dict[str, str]) -> Callable[..., str]:
    def make(price: int = 500000) -> str:
        return create_paid_event(client, organizer_headers, price)

    return make


@pytest.fixture
def complete_checklist(
    client: TestClient, organizer_headers: dict[str, str]
) -> Callable[[str], None]:
    def complete(event_id: str) -> None:
        complete_activation_checklist(client, organizer_headers, event_id)

    return complete


@pytest.fixture
def paid_event_id(client: TestClient, organizer_headers: dict[str, str]) -> str:
    """An event whose paid sales are active, so paid orders can be placed."""
    event_id = create_paid_event(client, organizer_headers)
    complete_activation_checklist(client, organizer_headers, event_id)
    response = client.post(
        f"/api/v1/paid-sales/activate?event_id={event_id}", headers=organizer_headers
    )
    assert response.status_code == 200, response.json()
    return event_id
