import secrets
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select

import core
from core import Session
from features.audit_log.models import AuditLog
from features.audit_log.service import audit_log_service
from features.auth.service import auth_service
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.orders.models import Order
from features.promo.models import PromoCampaign
from features.promo.service import promo_service
from features.tickets.models import Ticket
from features.tickets.service import ticket_service
from features.users.models import User
from features.venues.models import Venue


@dataclass
class ScannerData:
    event_id: UUID
    other_event_id: UUID
    ticket_id: UUID
    order_id: UUID
    worker_id: UUID
    owner_id: UUID
    qr_token: str
    owner_headers: dict[str, str]
    worker_headers: dict[str, str]
    outsider_headers: dict[str, str]

    @property
    def params(self) -> dict[str, str]:
        return {"event_id": str(self.event_id), "ticket_id": str(self.ticket_id)}


def seed_scanner(db: Session) -> ScannerData:
    owner = User(
        email="owner@scanner.test",
        full_name="Owner",
        password_hash="unused",
        role="organizer",
        is_email_verified=True,
    )
    worker = User(email="worker@scanner.test", full_name="Scanner", password_hash="unused")
    outsider = User(email="other@scanner.test", full_name="Outsider", password_hash="unused")
    venue = Venue(name="Hall", address="Almaty")
    db.add_all([owner, worker, outsider, venue])
    db.flush()
    events = [
        Event(
            title=title,
            category="Technology",
            venue_id=venue.id,
            organizer_id=owner.id,
            capacity=100,
            status="published",
            start_time=core.time_now(),
            end_time=core.time_now() + timedelta(hours=2),
        )
        for title in ("Scanner event", "Other event")
    ]
    db.add_all(events)
    db.flush()
    order = Order(
        event_id=events[0].id,
        customer_name="Attendee",
        customer_email="attendee@scanner.test",
        status="paid",
    )
    db.add(order)
    db.flush()
    ticket = Ticket(
        order_id=order.id,
        order_item_id=uuid4(),
        event_id=events[0].id,
        ticket_type_id=uuid4(),
        ticket_type_name="Entry",
        attendee_name="Attendee",
        attendee_email="attendee@scanner.test",
        qr_token=secrets.token_hex(32),
    )
    db.add(ticket)
    db.add(StaffAssignment(event_id=events[0].id, user_id=worker.id))
    db.flush()
    data = ScannerData(
        event_id=events[0].id,
        other_event_id=events[1].id,
        ticket_id=ticket.id,
        order_id=order.id,
        worker_id=worker.id,
        owner_id=owner.id,
        qr_token=ticket.qr_token,
        owner_headers={"Authorization": f"Bearer {auth_service.create_access_token(owner)}"},
        worker_headers={"Authorization": f"Bearer {auth_service.create_access_token(worker)}"},
        outsider_headers={"Authorization": f"Bearer {auth_service.create_access_token(outsider)}"},
    )
    db.commit()
    return data


@pytest.fixture
def scanner(client: TestClient) -> ScannerData:
    assert core.engine is not None
    with Session(core.engine) as db:
        return seed_scanner(db)


@pytest.mark.parametrize("path", ["verify", "check-in", "undo-check-in"])
def test_scanner_requires_auth_and_event_access(
    client: TestClient, scanner: ScannerData, path: str
) -> None:
    method = "GET" if path == "verify" else "POST"
    params = {**scanner.params, "qr_token": scanner.qr_token}
    url = f"/api/v1/tickets/{path}"
    assert client.request(method, url, params=params).status_code == 401
    assert (
        client.request(method, url, params=params, headers=scanner.outsider_headers).status_code
        == 404
    )


def test_wrong_event_returns_no_ticket_data(client: TestClient, scanner: ScannerData) -> None:
    params = {
        **scanner.params,
        "event_id": str(scanner.other_event_id),
        "qr_token": scanner.qr_token,
    }
    response = client.get("/api/v1/tickets/verify", params=params, headers=scanner.owner_headers)
    assert response.json()["valid"] is False
    assert response.json()["ticket"] is None
    for path in ("check-in", "undo-check-in"):
        assert (
            client.post(
                f"/api/v1/tickets/{path}", params=params, headers=scanner.owner_headers
            ).status_code
            == 404
        )


def test_scanner_permissions_audit_and_revocation(client: TestClient, scanner: ScannerData) -> None:
    result = client.post(
        "/api/v1/tickets/check-in", params=scanner.params, headers=scanner.worker_headers
    )
    assert result.status_code == 200
    assert result.json()["checked_in_at"] is not None
    assert (
        client.post(
            "/api/v1/tickets/undo-check-in", params=scanner.params, headers=scanner.worker_headers
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/tickets/check-in", params=scanner.params, headers=scanner.worker_headers
        ).status_code
        == 400
    )
    assert core.engine is not None
    with Session(core.engine) as db:
        assignment = db.scalars(select(StaffAssignment)).one()
        assignment.can_undo_check_in = True
        db.commit()
        assignment_id = str(assignment.id)
    reversed_ticket = client.post(
        "/api/v1/tickets/undo-check-in", params=scanner.params, headers=scanner.worker_headers
    )
    assert reversed_ticket.status_code == 200
    assert reversed_ticket.json()["status"] == "valid"
    assert reversed_ticket.json()["checked_in_at"] is None
    with Session(core.engine) as db:
        logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at)).all()
        assert [log.action for log in logs] == ["ticket_checked_in", "ticket_check_in_reversed"]
        assert all(log.actor_id == scanner.worker_id for log in logs)
        assert all(
            log.event_id == scanner.event_id and log.entity_id == scanner.ticket_id for log in logs
        )
    removed = client.delete(
        "/api/v1/checkin/staff",
        headers=scanner.owner_headers,
        params={"event_id": str(scanner.event_id), "assignment_id": assignment_id},
    )
    assert removed.status_code == 204
    assert (
        client.post(
            "/api/v1/tickets/check-in", params=scanner.params, headers=scanner.worker_headers
        ).status_code
        == 404
    )


@pytest.mark.parametrize("order_status", ["pending", "cancelled", "refunded"])
def test_non_paid_orders_cannot_enter_or_be_restored(
    client: TestClient, scanner: ScannerData, order_status: str
) -> None:
    assert core.engine is not None
    with Session(core.engine) as db:
        order = db.get(Order, scanner.order_id)
        assert order is not None
        order.status = order_status
        db.commit()
    response = client.get(
        "/api/v1/tickets/verify",
        headers=scanner.worker_headers,
        params={"event_id": str(scanner.event_id), "qr_token": scanner.qr_token},
    )
    assert response.json()["valid"] is False
    assert response.json()["status"] == order_status
    assert (
        client.post(
            "/api/v1/tickets/check-in", params=scanner.params, headers=scanner.worker_headers
        ).status_code
        == 400
    )
    with Session(core.engine) as db:
        ticket = db.get(Ticket, scanner.ticket_id)
        assert ticket is not None
        ticket.status = "checked_in"
        ticket.checked_in_at = core.time_now()
        db.commit()
    assert (
        client.post(
            "/api/v1/tickets/undo-check-in", params=scanner.params, headers=scanner.owner_headers
        ).status_code
        == 400
    )
    with Session(core.engine) as db:
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 0


@pytest.mark.parametrize("ticket_status", ["checked_in", "cancelled", "refunded"])
def test_non_valid_tickets_are_rejected(
    client: TestClient, scanner: ScannerData, ticket_status: str
) -> None:
    assert core.engine is not None
    with Session(core.engine) as db:
        ticket = db.get(Ticket, scanner.ticket_id)
        assert ticket is not None
        ticket.status = ticket_status
        db.commit()
    response = client.get(
        "/api/v1/tickets/verify",
        headers=scanner.worker_headers,
        params={"event_id": str(scanner.event_id), "qr_token": scanner.qr_token},
    )
    assert response.json()["valid"] is False
    assert response.json()["status"] == ticket_status
    assert (
        client.post(
            "/api/v1/tickets/check-in", params=scanner.params, headers=scanner.worker_headers
        ).status_code
        == 400
    )


@pytest.mark.parametrize("event_status", ["cancelled", "suspended"])
def test_unavailable_event_and_campaign_qr_are_rejected(
    client: TestClient, scanner: ScannerData, event_status: str
) -> None:
    assert core.engine is not None
    with Session(core.engine) as db:
        campaign = PromoCampaign(
            event_id=scanner.event_id,
            name="Promo",
            code="TESTCODE",
            qr_token=secrets.token_urlsafe(32),
            discount_type="percent",
            discount_value=10,
        )
        db.add(campaign)
        db.flush()
        tokens = [campaign.qr_token, promo_service.campaign_link(campaign)]
        campaign_id = str(campaign.id)
        db.commit()
    for token in tokens:
        response = client.get(
            "/api/v1/tickets/verify",
            headers=scanner.worker_headers,
            params={"event_id": str(scanner.event_id), "qr_token": token},
        )
        assert response.json()["valid"] is False
        assert response.json()["ticket"] is None
    assert (
        client.post(
            "/api/v1/tickets/check-in",
            headers=scanner.worker_headers,
            params={**scanner.params, "ticket_id": campaign_id},
        ).status_code
        == 404
    )
    with Session(core.engine) as db:
        event = db.get(Event, scanner.event_id)
        assert event is not None
        event.status = event_status
        db.commit()
    assert client.get("/api/v1/checkin/events", headers=scanner.worker_headers).json() == []
    for path in ("verify", "check-in", "undo-check-in"):
        method = "GET" if path == "verify" else "POST"
        assert (
            client.request(
                method,
                f"/api/v1/tickets/{path}",
                headers=scanner.owner_headers,
                params={**scanner.params, "qr_token": scanner.qr_token},
            ).status_code
            == 400
        )


@pytest.mark.parametrize("reverse", [False, True])
def test_simultaneous_scans_or_undos_only_succeed_once(tmp_path: Path, reverse: bool) -> None:
    # Separate connections to a real file: an in-memory StaticPool would share one connection.
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.sqlite'}")
    try:
        core.DbBase.metadata.create_all(engine)
        with Session(engine) as db:
            data = seed_scanner(db)
            if reverse:
                ticket = db.get(Ticket, data.ticket_id)
                assert ticket is not None
                ticket_service.check_in_ticket(db, ticket, actor_id=data.owner_id)
        barrier = Barrier(2, timeout=10)

        def scan() -> int:
            with Session(engine) as db:
                ticket = db.get(Ticket, data.ticket_id)
                assert ticket is not None
                barrier.wait()
                try:
                    if reverse:
                        ticket_service.undo_check_in(db, ticket, actor_id=data.owner_id)
                    else:
                        ticket_service.check_in_ticket(db, ticket, actor_id=data.owner_id)
                except HTTPException as error:
                    return error.status_code
                return 200

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: scan(), range(2)))
        assert sorted(results) == [200, 400]
        with Session(engine) as db:
            action = "ticket_check_in_reversed" if reverse else "ticket_checked_in"
            assert (
                db.scalar(
                    select(func.count())
                    .select_from(AuditLog)
                    .where(
                        AuditLog.action == action,
                    )
                )
                == 1
            )
    finally:
        engine.dispose()


def test_stale_undo_cannot_reverse_a_later_admission(scanner: ScannerData) -> None:
    assert core.engine is not None
    with Session(core.engine) as db:
        ticket = db.get(Ticket, scanner.ticket_id)
        assert ticket is not None
        ticket_service.check_in_ticket(db, ticket, actor_id=scanner.owner_id)
    with Session(core.engine) as stale_db, Session(core.engine) as db:
        stale_ticket = stale_db.get(Ticket, scanner.ticket_id)
        current_ticket = db.get(Ticket, scanner.ticket_id)
        assert stale_ticket is not None and current_ticket is not None
        ticket_service.undo_check_in(db, current_ticket, actor_id=scanner.owner_id)
        ticket_service.check_in_ticket(db, current_ticket, actor_id=scanner.owner_id)
        with pytest.raises(HTTPException) as denied:
            ticket_service.undo_check_in(stale_db, stale_ticket, actor_id=scanner.owner_id)
        assert denied.value.status_code == 400
        db.refresh(current_ticket)
        assert current_ticket.status == "checked_in"


def test_audit_failure_rolls_back_admission(
    scanner: ScannerData, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Audit write failed")

    monkeypatch.setattr(audit_log_service, "record", fail_audit)
    assert core.engine is not None
    with pytest.raises(RuntimeError, match="Audit write failed"), Session(core.engine) as db:
        ticket = db.get(Ticket, scanner.ticket_id)
        assert ticket is not None
        ticket_service.check_in_ticket(db, ticket, actor_id=scanner.owner_id)
    with Session(core.engine) as db:
        persisted = db.get(Ticket, scanner.ticket_id)
        assert persisted is not None
        assert persisted.status == "valid"
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 0
