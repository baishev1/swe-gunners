from datetime import timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

import core
from core import Session
from features.auth.service import auth_service
from features.events.models import Event
from features.users.models import User
from features.venues.models import Venue


def account(client: TestClient, role: str = "attendee") -> tuple[UUID, dict[str, str]]:
    email = f"{uuid4()}@example.com"
    password = "part-five-test-password"
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test user",
            "role": role,
        },
    )
    assert registered.status_code == 201
    logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert logged_in.status_code == 200
    return UUID(registered.json()["id"]), {
        "Authorization": f"Bearer {logged_in.json()['access_token']}",
    }


def event_for(owner_id: UUID) -> UUID:
    assert core.engine is not None
    with Session(core.engine) as db:
        venue = Venue(name="Staff test venue", address="Almaty")
        db.add(venue)
        db.flush()
        event = Event(
            title="Staff test",
            category="Technology",
            venue_id=venue.id,
            organizer_id=owner_id,
            capacity=100,
            status="published",
            start_time=core.time_now(),
            end_time=core.time_now() + timedelta(hours=2),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event.id


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/support/cases", None),
        (
            "POST",
            "/support/cases",
            {
                "target": "platform",
                "subject": "Help",
                "category": "technical",
                "message": "Help",
            },
        ),
        ("GET", "/support/cases/detail", None),
        ("GET", "/support/messages", None),
        ("POST", "/support/messages", {"body": "Hello"}),
        ("PATCH", "/support/cases/status", {"status": "resolved"}),
        ("POST", "/support/cases/assign", None),
        ("GET", "/checkin/events", None),
        ("GET", "/checkin/staff", None),
        ("POST", "/checkin/staff", {"user_id": str(uuid4())}),
        ("DELETE", "/checkin/staff", None),
    ],
)
def test_all_part5_routes_require_a_login(
    client: TestClient, method: str, path: str, body: dict[str, str] | None
) -> None:
    response = client.request(
        method,
        f"/api/v1{path}",
        json=body,
        params={
            "event_id": str(uuid4()),
            "case_id": str(uuid4()),
            "assignment_id": str(uuid4()),
        },
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_jwt_staff_and_support_access_and_revocation(client: TestClient) -> None:
    owner_id, owner = account(client, "organizer")
    worker_id, worker = account(client)
    requester_id, requester = account(client)
    _, outsider = account(client, "organizer")
    event_id = event_for(owner_id)
    event_params = {"event_id": str(event_id)}
    assignment_body = {"user_id": str(worker_id), "can_manage_support": True}

    assert (
        client.post(
            "/api/v1/checkin/staff", headers=outsider, params=event_params, json=assignment_body
        ).status_code
        == 404
    )
    assignment = client.post(
        "/api/v1/checkin/staff", headers=owner, params=event_params, json=assignment_body
    )
    assert assignment.status_code == 201
    assert client.get("/api/v1/checkin/events", headers=outsider).json() == []
    assert [e["id"] for e in client.get("/api/v1/checkin/events", headers=worker).json()] == [
        str(event_id),
    ]
    assert (
        client.get("/api/v1/checkin/staff", headers=worker, params=event_params).status_code == 404
    )

    created = client.post(
        "/api/v1/support/cases",
        headers=requester,
        json={
            "target": "organizer",
            "event_id": str(event_id),
            "category": "technical",
            "subject": "Need help",
            "message": "Can you help?",
        },
    )
    assert created.status_code == 201
    assert created.json()["requester_id"] == str(requester_id)
    case_params = {"case_id": created.json()["id"]}
    assert client.get("/api/v1/support/cases", headers=outsider).json() == []
    assert (
        client.get("/api/v1/support/messages", headers=outsider, params=case_params).status_code
        == 404
    )
    assert (
        client.patch(
            "/api/v1/support/cases/status",
            headers=requester,
            params=case_params,
            json={"status": "resolved"},
        ).status_code
        == 403
    )
    reply = client.post(
        "/api/v1/support/messages",
        headers=worker,
        params=case_params,
        json={"body": "Yes, I can help"},
    )
    assert reply.status_code == 201
    assert reply.json()["author_id"] == str(worker_id)
    assert (
        client.patch(
            "/api/v1/support/cases/status",
            headers=worker,
            params=case_params,
            json={"status": "resolved"},
        ).status_code
        == 200
    )

    removed = client.delete(
        "/api/v1/checkin/staff",
        headers=owner,
        params={
            **event_params,
            "assignment_id": assignment.json()["id"],
        },
    )
    assert removed.status_code == 204
    # The same JWT remains valid; the assignment is checked again on each request.
    assert client.get("/api/v1/checkin/events", headers=worker).json() == []
    assert (
        client.get("/api/v1/support/messages", headers=worker, params=case_params).status_code
        == 404
    )
    assert (
        len(client.get("/api/v1/support/messages", headers=requester, params=case_params).json())
        == 2
    )


@pytest.mark.parametrize(
    "token_kind", ["garbage", "expired", "deleted", "disabled", "verify", "reset"]
)
def test_part5_rejects_unusable_tokens(client: TestClient, token_kind: str) -> None:
    user_id, headers = account(client)
    assert core.engine is not None
    with Session(core.engine) as db:
        user = db.get(User, user_id)
        assert user is not None
        if token_kind == "garbage":
            headers = {"Authorization": "Bearer garbage"}
        elif token_kind == "expired":
            token = jwt.encode(
                {"sub": str(user_id), "exp": core.time_now() - timedelta(minutes=1)},
                core.settings.JWT_SECRET,
                algorithm=core.settings.JWT_ALGORITHM,
            )
            headers = {"Authorization": f"Bearer {token}"}
        elif token_kind == "deleted":
            db.delete(user)
            db.commit()
        elif token_kind == "disabled":
            user.is_active = False
            db.commit()
        elif token_kind == "verify":
            headers = {"Authorization": f"Bearer {auth_service.create_verify_token(user)}"}
        elif token_kind == "reset":
            headers = {"Authorization": f"Bearer {auth_service.create_reset_token(user)}"}

    for path in ("/api/v1/support/cases", "/api/v1/checkin/events", "/api/v1/auth/me"):
        response = client.get(path, headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
