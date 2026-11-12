from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import core
from core import Session
from features.checkin.guards import assigned_event, undo_check_in_event
from features.events.models import Event
from features.users.models import User


def event_for(client: TestClient, owner: User) -> str:
    venue = client.post("/api/v1/venues", json={"name": "Hall", "address": "Almaty"}).json()
    now = datetime.now(UTC)
    event = client.post(
        "/api/v1/events",
        params={"organizer_id": str(owner.id)},
        json={
            "title": "Staff event",
            "category": "Technology",
            "venue_id": venue["id"],
            "capacity": 100,
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        },
    )
    assert event.status_code == 201
    return event.json()["id"]


def test_staff_and_event_lists_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/checkin/events").status_code == 401
    assert client.get("/api/v1/checkin/staff", params={"event_id": str(uuid4())}).status_code == 401


def test_staff_assignment_revocation_and_scanner_permissions(
    client: TestClient, login: Callable[[str], User]
) -> None:
    worker = login("other")
    owner = login("organizer")
    event_id = event_for(client, owner)
    params = {"event_id": event_id}
    result = client.post("/api/v1/checkin/staff", params=params, json={"user_id": str(worker.id)})
    assert result.status_code == 201
    assignment = result.json()
    assert not assignment["can_undo_check_in"]
    assert not assignment["can_manage_support"]
    assert len(client.get("/api/v1/checkin/staff", params=params).json()) == 1
    assert (
        client.post(
            "/api/v1/checkin/staff", params=params, json={"user_id": str(worker.id)}
        ).status_code
        == 409
    )
    login("other")
    assert [e["id"] for e in client.get("/api/v1/checkin/events").json()] == [event_id]
    assert client.get("/api/v1/checkin/staff", params=params).status_code == 404
    assert (
        client.delete(
            "/api/v1/checkin/staff", params={**params, "assignment_id": assignment["id"]}
        ).status_code
        == 404
    )
    assert core.engine is not None
    with Session(core.engine) as db:
        event = assigned_event(event_id=UUID(event_id), user=worker, db=db)
        with pytest.raises(HTTPException) as denied:
            undo_check_in_event(event=event, user=worker, db=db)
        assert denied.value.status_code == 403

    login("organizer")
    assert (
        client.delete(
            "/api/v1/checkin/staff", params={**params, "assignment_id": assignment["id"]}
        ).status_code
        == 204
    )
    login("other")
    assert client.get("/api/v1/checkin/events").json() == []
    with Session(core.engine) as db:
        with pytest.raises(HTTPException) as denied:
            assigned_event(event_id=UUID(event_id), user=worker, db=db)
        assert denied.value.status_code == 404


def test_staff_cannot_manage_other_event_and_assignment_ids_are_scoped(
    client: TestClient, login: Callable[[str], User]
) -> None:
    worker = login("other")
    event_id = event_for(client, login("organizer"))
    result = client.post(
        "/api/v1/checkin/staff",
        params={"event_id": event_id},
        json={
            "user_id": str(worker.id),
            "can_undo_check_in": True,
        },
    )
    assignment_id = result.json()["id"]
    other_owner = login("other_organizer")
    other_event = event_for(client, other_owner)
    assert (
        client.post(
            "/api/v1/checkin/staff",
            params={"event_id": event_id},
            json={
                "user_id": str(worker.id),
            },
        ).status_code
        == 404
    )
    assert (
        client.delete(
            "/api/v1/checkin/staff",
            params={
                "event_id": other_event,
                "assignment_id": assignment_id,
            },
        ).status_code
        == 404
    )
    assert core.engine is not None
    with Session(core.engine) as db:
        event = assigned_event(event_id=UUID(event_id), user=worker, db=db)
        assert undo_check_in_event(event=event, user=worker, db=db).id == event.id
        with pytest.raises(HTTPException) as denied:
            assigned_event(event_id=UUID(other_event), user=worker, db=db)
        assert denied.value.status_code == 404


def test_staff_input_validation_and_inactive_users(
    client: TestClient, login: Callable[[str], User]
) -> None:
    worker = login("other")
    owner = login("organizer")
    event_id = event_for(client, owner)
    params = {"event_id": event_id}
    assert (
        client.post(
            "/api/v1/checkin/staff",
            params=params,
            json={
                "user_id": str(uuid4()),
            },
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/checkin/staff",
            params=params,
            json={
                "user_id": str(owner.id),
            },
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/checkin/staff",
            params=params,
            json={
                "user_id": str(worker.id),
                "role": "platform_admin",
            },
        ).status_code
        == 422
    )
    assert core.engine is not None
    with Session(core.engine) as db:
        persisted = db.get(User, worker.id)
        assert persisted is not None
        persisted.is_active = False
        db.commit()
    assert (
        client.post(
            "/api/v1/checkin/staff",
            params=params,
            json={
                "user_id": str(worker.id),
            },
        ).status_code
        == 400
    )
    worker.is_active = False
    login("other")
    assert client.get("/api/v1/checkin/events").status_code == 403


def test_owner_admin_and_cancelled_event_access(
    client: TestClient, login: Callable[[str], User]
) -> None:
    worker = login("other")
    owner = login("organizer")
    event_id = event_for(client, owner)
    assert [e["id"] for e in client.get("/api/v1/checkin/events").json()] == [event_id]
    client.post(
        "/api/v1/checkin/staff",
        params={"event_id": event_id},
        json={
            "user_id": str(worker.id),
            "can_undo_check_in": True,
        },
    )
    admin = login("admin")
    assert client.get("/api/v1/checkin/staff", params={"event_id": event_id}).status_code == 200
    assert core.engine is not None
    with Session(core.engine) as db:
        for user in (owner, admin):
            event = assigned_event(event_id=UUID(event_id), user=user, db=db)
            assert undo_check_in_event(event=event, user=user, db=db).id == UUID(event_id)
        cancelled_event = db.get(Event, UUID(event_id))
        assert cancelled_event is not None
        cancelled_event.status = "cancelled"
        db.commit()
        with pytest.raises(HTTPException) as denied:
            assigned_event(event_id=UUID(event_id), user=worker, db=db)
        assert denied.value.status_code == 400
    login("other")
    assert client.get("/api/v1/checkin/events").json() == []


def test_support_staff_permission_is_event_scoped_and_revocable(
    client: TestClient, login: Callable[[str], User]
) -> None:
    worker = login("other")
    owner = login("organizer")
    event_id = event_for(client, owner)
    client.post("/api/v1/events/publish", params={"event_id": event_id})
    assignment = client.post(
        "/api/v1/checkin/staff",
        params={"event_id": event_id},
        json={
            "user_id": str(worker.id),
            "can_manage_support": True,
        },
    ).json()
    # A platform case stays private even when it refers to the assigned event.
    platform_case = client.post(
        "/api/v1/support/cases",
        json={
            "target": "platform",
            "event_id": event_id,
            "category": "activation",
            "subject": "Activation",
            "message": "Help",
        },
    ).json()
    login("attendee")
    case = client.post(
        "/api/v1/support/cases",
        json={
            "target": "organizer",
            "event_id": event_id,
            "category": "technical",
            "subject": "Help",
            "message": "Help please",
        },
    ).json()
    login("other")
    assert [c["id"] for c in client.get("/api/v1/support/cases").json()] == [case["id"]]
    assert (
        client.get(
            "/api/v1/support/cases/detail",
            params={
                "case_id": platform_case["id"],
            },
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/support/messages",
            params={"case_id": case["id"]},
            json={
                "body": "I can help",
            },
        ).status_code
        == 201
    )
    assert (
        client.patch(
            "/api/v1/support/cases/status",
            params={"case_id": case["id"]},
            json={
                "status": "in_progress",
            },
        ).status_code
        == 200
    )
    login("organizer")
    client.delete(
        "/api/v1/checkin/staff",
        params={
            "event_id": event_id,
            "assignment_id": assignment["id"],
        },
    )
    # Scanner access alone must not grant access to support conversations.
    client.post(
        "/api/v1/checkin/staff",
        params={"event_id": event_id},
        json={
            "user_id": str(worker.id),
        },
    )
    login("other")
    assert client.get("/api/v1/support/cases").json() == []
    assert client.get("/api/v1/support/messages", params={"case_id": case["id"]}).status_code == 404
