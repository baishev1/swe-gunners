from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from features.users.models import User


def support_event(client: TestClient, owner: User, visibility: str = "public") -> str:
    venue = client.post("/api/v1/venues", json={"name": "Hall", "address": "Almaty"})
    now = datetime.now(UTC)
    response = client.post(
        "/api/v1/events",
        params={"organizer_id": str(owner.id)},
        json={
            "title": "Support test event",
            "category": "Technology",
            "venue_id": venue.json()["id"],
            "capacity": 100,
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=2)).isoformat(),
            "visibility": visibility,
        },
    )
    assert response.status_code == 201
    event_id = response.json()["id"]
    assert client.post("/api/v1/events/publish", params={"event_id": event_id}).status_code == 200
    return event_id


def open_case(client: TestClient, event_id: str) -> str:
    response = client.post(
        "/api/v1/support/cases",
        json={
            "target": "organizer",
            "event_id": event_id,
            "category": "ticket_delivery",
            "subject": "Missing ticket",
            "message": "Please help me find my ticket.",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_support_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/support/cases")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_support_conversation_and_staff_management(
    client: TestClient, login: Callable[[str], User]
) -> None:
    owner = login("organizer")
    event_id = support_event(client, owner)
    requester = login("attendee")
    case_id = open_case(client, event_id)
    params = {"case_id": case_id}
    messages = client.get("/api/v1/support/messages", params=params).json()
    assert len(messages) == 1
    assert messages[0]["author_id"] == str(requester.id)
    assert messages[0]["body"] == "Please help me find my ticket."

    assert (
        client.patch(
            "/api/v1/support/cases/status", params=params, json={"status": "resolved"}
        ).status_code
        == 403
    )
    assert client.post("/api/v1/support/cases/assign", params=params).status_code == 403

    login("organizer")
    assert client.post("/api/v1/support/cases/assign", params=params).json()["assignee_id"] == str(
        owner.id
    )
    for status in ("in_progress", "waiting_for_customer", "resolved", "open"):
        result = client.patch(
            "/api/v1/support/cases/status", params=params, json={"status": status}
        )
        assert result.status_code == 200
        assert result.json()["status"] == status
    reply = client.post(
        "/api/v1/support/messages", params=params, json={"body": "Check your inbox"}
    )
    assert reply.status_code == 201
    assert reply.json()["author_id"] == str(owner.id)

    login("attendee")
    assert len(client.get("/api/v1/support/messages", params=params).json()) == 2
    page = client.get("/api/v1/support/messages", params={**params, "offset": 1, "limit": 1})
    assert [m["body"] for m in page.json()] == ["Check your inbox"]


@pytest.mark.parametrize("outsider", ["other", "other_organizer"])
def test_support_prevents_cross_user_and_cross_event_access(
    client: TestClient, login: Callable[[str], User], outsider: str
) -> None:
    event_id = support_event(client, login("organizer"))
    login("attendee")
    case_id = open_case(client, event_id)
    login(outsider)
    params = {"case_id": case_id}
    assert client.get("/api/v1/support/cases").json() == []
    for path in ("/cases/detail", "/messages"):
        assert client.get(f"/api/v1/support{path}", params=params).status_code == 404
    assert (
        client.post(
            "/api/v1/support/messages", params=params, json={"body": "Intrusion"}
        ).status_code
        == 404
    )
    assert (
        client.patch(
            "/api/v1/support/cases/status", params=params, json={"status": "resolved"}
        ).status_code
        == 404
    )
    assert client.post("/api/v1/support/cases/assign", params=params).status_code == 404


def test_platform_support_is_only_visible_to_requester_and_admin(
    client: TestClient, login: Callable[[str], User]
) -> None:
    owner = login("organizer")
    event_id = support_event(client, owner)
    payload = {
        "target": "platform",
        "event_id": event_id,
        "category": "activation",
        "subject": "Cannot activate sales",
        "message": "Activation failed.",
    }
    login("attendee")
    assert client.post("/api/v1/support/cases", json=payload).status_code == 403
    login("other_organizer")
    assert client.post("/api/v1/support/cases", json=payload).status_code == 403
    login("organizer")
    result = client.post("/api/v1/support/cases", json=payload)
    assert result.status_code == 201
    params = {"case_id": result.json()["id"]}
    login("other_organizer")
    assert client.get("/api/v1/support/cases/detail", params=params).status_code == 404
    admin = login("admin")
    assert len(client.get("/api/v1/support/cases").json()) == 1
    assert client.post("/api/v1/support/cases/assign", params=params).json()["assignee_id"] == str(
        admin.id
    )


def test_case_context_and_input_validation(
    client: TestClient, login: Callable[[str], User]
) -> None:
    event_id = support_event(client, login("organizer"), visibility="private")
    login("attendee")
    payload = {
        "target": "organizer",
        "event_id": event_id,
        "category": "technical",
        "subject": "Help",
        "message": "Something went wrong",
    }
    assert client.post("/api/v1/support/cases", json=payload).status_code == 404
    payload["event_id"] = str(uuid4())
    assert client.post("/api/v1/support/cases", json=payload).status_code == 404
    payload.pop("event_id")
    assert client.post("/api/v1/support/cases", json=payload).status_code == 422
    login("organizer")
    payload["target"] = "platform"
    payload["message"] = "  \n "
    assert client.post("/api/v1/support/cases", json=payload).status_code == 422
    payload["message"] = "Help"
    payload["requester_id"] = str(uuid4())
    assert client.post("/api/v1/support/cases", json=payload).status_code == 422


def test_inactive_user_cannot_access_support(
    client: TestClient, login: Callable[[str], User]
) -> None:
    user = login("attendee")
    user.is_active = False
    assert client.get("/api/v1/support/cases").status_code == 403


def test_message_and_status_validation(client: TestClient, login: Callable[[str], User]) -> None:
    event_id = support_event(client, login("organizer"))
    case_id = open_case(client, event_id)
    params = {"case_id": case_id}
    for body in (" ", "a" * 5001):
        assert (
            client.post("/api/v1/support/messages", params=params, json={"body": body}).status_code
            == 422
        )
    assert (
        client.patch(
            "/api/v1/support/cases/status", params=params, json={"status": "invalid"}
        ).status_code
        == 422
    )
    assert (
        client.get("/api/v1/support/messages", params={**params, "limit": 101}).status_code == 422
    )
