from sqlalchemy import func, select

import core
from core import *
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.events.service import event_service
from features.orders.models import Order
from features.paid_sales.service import paid_sales_service
from features.promo.models import PromoCampaign
from features.tickets.models import Ticket
from features.users.models import User
from scripts.seed import (
    CANCELLED_EVENT_TITLE,
    EVENT_TITLE,
    FREE_EVENT_TITLE,
    PAST_EVENT_TITLE,
    PROMO_CODE,
    SEATED_EVENT_TITLE,
    seed,
)


def count(db: Session, model: type) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


def test_seed_is_idempotent(client) -> None:
    with Session(core.engine) as db:
        seed(db)
        counts = {m: count(db, m) for m in (User, Event, Order, Ticket, PromoCampaign)}
        seed(db)

        assert {m: count(db, m) for m in counts} == counts


def test_seed_covers_every_demo_scenario(client) -> None:
    with Session(core.engine) as db:
        seed(db)
        events = {e.title: e for e in db.scalars(select(Event))}

        now = time_now()
        phases = {title: event_service.event_phase(e, now) for title, e in events.items()}
        assert phases[FREE_EVENT_TITLE] == "upcoming"
        assert phases[EVENT_TITLE] == "upcoming"
        assert phases[PAST_EVENT_TITLE] == "completed"
        assert phases[CANCELLED_EVENT_TITLE] == "cancelled"

        paid_event = events[EVENT_TITLE]
        assert paid_sales_service.is_open(db, paid_event.id)
        campaign = db.scalar(select(PromoCampaign).where(PromoCampaign.code == PROMO_CODE))
        assert campaign is not None and campaign.redemption_count == 2

        staff = db.scalar(select(User).where(User.role == "event_admin"))
        assert staff is not None
        assigned = set(
            db.scalars(select(StaffAssignment.event_id).where(StaffAssignment.user_id == staff.id))
        )
        assert {paid_event.id, events[FREE_EVENT_TITLE].id} <= assigned

        def statuses(event: Event) -> set[str]:
            return set(db.scalars(select(Order.status).where(Order.event_id == event.id)))

        assert statuses(paid_event) == {"paid"}
        assert statuses(events[CANCELLED_EVENT_TITLE]) == {"refunded"}
        checked_in = db.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.event_id == events[PAST_EVENT_TITLE].id, Ticket.status == "checked_in")
        )
        assert checked_in == 4

        seated_event = events[SEATED_EVENT_TITLE]
        assert seated_event.is_assigned_seating is True
        assert seated_event.id in assigned
        seated_tickets = db.scalars(
            select(Ticket).where(Ticket.event_id == seated_event.id)
        ).all()
        assert len(seated_tickets) == 4
        assert all(t.section and t.row and t.seat for t in seated_tickets)

        ga_tickets = db.scalars(
            select(Ticket).where(Ticket.event_id == paid_event.id)
        ).all()
        assert ga_tickets
        assert all(t.section is None and t.row is None and t.seat is None for t in ga_tickets)
