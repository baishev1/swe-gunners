"""Demo data for local runs and the term demonstration.

`uv run python -m scripts.seed` gives every SRS §11 scenario something to show:
a free event, a paid event with completed activation, a promo campaign, staff for
the mobile scanner, a completed and a cancelled event with history, and paid
orders so analytics are not empty. Events are matched by title, so running the
script again changes nothing.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select, update

import core
from core import *
from features.auth.service import hasher
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.events.service import event_service
from features.orders.models import Order
from features.orders.schemas import OrderCreate, OrderItemCreate
from features.orders.service import order_service
from features.organizers.models import OrganizerProfile
from features.paid_sales.service import paid_sales_service
from features.payments.models import Payment
from features.payments.service import payment_service
from features.promo.models import PromoCampaign
from features.promo.schemas import PromoCampaignCreate
from features.promo.service import promo_service
from features.seating.layouts import MAIN_HALL
from features.seating.schemas import SeatCategoryPrice, SeatingSetupRequest
from features.seating.service import seating_service
from features.ticket_types.models import TicketType
from features.ticket_types.schemas import TicketTypeCreate
from features.ticket_types.service import ticket_type_service
from features.tickets.models import Ticket
from features.tickets.service import ticket_service
from features.users.models import User
from features.venues.models import Venue

PASSWORD = "password123"

USERS = [
    ("attendee@biletflow.dev", "Demo Attendee", "attendee"),
    ("organizer@biletflow.dev", "Demo Organizer", "organizer"),
    ("eventadmin@biletflow.dev", "Demo Event Admin", "event_admin"),
    ("admin@biletflow.dev", "Demo Platform Admin", "platform_admin"),
]

# Buyers for the generated orders; they get accounts so tickets show up under "My tickets".
BUYERS = [
    ("aigerim@biletflow.dev", "Айгерім Сейітова"),
    ("daniyar@biletflow.dev", "Данияр Омаров"),
    ("madina@biletflow.dev", "Мадина Ахметова"),
]

EVENT_TITLE = "BiletFlow Demo Concert"
SEATED_EVENT_TITLE = "Almaty Symphony Evening"
FREE_EVENT_TITLE = "Открытая лекция: Как запустить стартап в Казахстане"
PAST_EVENT_TITLE = "Jazz Evening Almaty"
CANCELLED_EVENT_TITLE = "Outdoor Cinema Night"
PROMO_CODE = "DEMO20"

KZT = 100  # Prices are stored in tiyn.

MAIN_HALL_ADDRESS = "53 Kabanbay Batyr Ave, Astana"

# Main Hall price categories: (category, ticket type name, price).
SEAT_PRICES = [
    (1, "Lower parterre", 12000 * KZT),
    (2, "Upper parterre", 8000 * KZT),
    (3, "Balcony", 4500 * KZT),
]


@dataclass
class Demo:
    users: dict[str, User]
    buyers: list[User]
    venue: Venue
    main_hall: Venue


def seed_user(db: Session, email: str, full_name: str, role: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=hasher.hash(PASSWORD),
            full_name=full_name,
            role=role,
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
    return user


def seed_organizer_profile(db: Session, user: User) -> None:
    """A profile that already passed the simulated identity and payout checks (SRS 3.2)."""
    profile = db.scalar(select(OrganizerProfile).where(OrganizerProfile.user_id == user.id))
    if profile is None:
        profile = OrganizerProfile(user_id=user.id, organization_name="Demo Events LLP")
        db.add(profile)
    profile.contact_email = profile.contact_email or user.email
    profile.payout_recipient_name = profile.payout_recipient_name or "Demo Events LLP"
    profile.payout_iban = profile.payout_iban or "KZ86125KZT5004100100"
    profile.payout_bin = profile.payout_bin or "123456789012"
    profile.identity_verified_at = profile.identity_verified_at or time_now()
    db.commit()


def seed_venue(db: Session) -> Venue:
    venue = db.scalar(select(Venue).where(Venue.name == "Demo Hall"))
    if venue is None:
        venue = Venue(name="Demo Hall", address="1 Abay Ave, Almaty")
        db.add(venue)
        db.commit()
    return venue


def seed_main_hall(db: Session) -> Venue:
    """The predefined assigned-seating layout (SRS 4.3.1), 1000 seats."""
    venue = db.scalar(select(Venue).where(Venue.layout_key == MAIN_HALL.key))
    if venue is None:
        venue = Venue(name=MAIN_HALL.name, address=MAIN_HALL_ADDRESS, layout_key=MAIN_HALL.key)
        db.add(venue)
        db.commit()
    return venue


def find_event(db: Session, title: str, organizer: User) -> Event | None:
    return db.scalar(select(Event).where(Event.title == title, Event.organizer_id == organizer.id))


def create_event(
    db: Session,
    demo: Demo,
    title: str,
    starts_in: timedelta,
    description: str,
    category: str,
    capacity: int,
    ticket_types: list[tuple[str, int, int]],
    is_assigned_seating: bool = False,
    venue: Venue | None = None,
) -> Event:
    """Creates and publishes an event through the services, so the timeline has entries."""
    organizer = demo.users["organizer"]
    start = time_now() + starts_in
    event = Event(
        title=title,
        description=description,
        category=category,
        venue_id=(venue or demo.venue).id,
        start_time=start,
        end_time=start + timedelta(hours=3),
        capacity=capacity,
        visibility="public",
        status="draft",
        organizer_id=organizer.id,
        is_assigned_seating=is_assigned_seating,
        refund_policy="Full refund up to 48 hours before the event.",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    for name, price, quantity in ticket_types:
        ticket_type_service.create_ticket_type(
            db, event, TicketTypeCreate(name=name, price=price, quantity=quantity), organizer.id
        )
    if is_assigned_seating:
        seating_service.setup(
            db,
            event,
            MAIN_HALL,
            SeatingSetupRequest(
                categories=[
                    SeatCategoryPrice(category=c, name=name, price=price)
                    for c, name, price in SEAT_PRICES
                ]
            ),
            organizer.id,
        )
    return event_service.publish_event(db, event, organizer.id)


def ticket_type_named(db: Session, event: Event, name: str) -> TicketType:
    ticket_type = db.scalar(
        select(TicketType).where(TicketType.event_id == event.id, TicketType.name == name)
    )
    assert ticket_type is not None
    return ticket_type


def place_order(
    db: Session,
    event: Event,
    buyer: User,
    items: list[tuple[TicketType, int | list[str]]],
    days_ago: float = 0,
    promo_code: str | None = None,
) -> Order:
    """Buys tickets like an attendee would: order, then a simulated payment if not free."""
    order = order_service.create_order(
        db,
        OrderCreate(
            event_id=event.id,
            customer_name=buyer.full_name,
            customer_email=buyer.email,
            # An int buys that many general-admission tickets, a list buys those seats.
            items=[
                OrderItemCreate(ticket_type_id=t.id, quantity=q)
                if isinstance(q, int)
                else OrderItemCreate(ticket_type_id=t.id, quantity=len(q), seats=q)
                for t, q in items
            ],
            promo_code=promo_code,
        ),
        buyer.id,
    )
    if order.status == "pending":
        payment_service.process_simulation(db, order)
    if days_ago:
        # Spread purchases out so "sales over time" has a shape.
        when = time_now() - timedelta(days=days_ago)
        db.execute(update(Order).where(Order.id == order.id).values(created_at=when))
        db.execute(update(Payment).where(Payment.order_id == order.id).values(created_at=when))
        db.execute(update(Ticket).where(Ticket.order_id == order.id).values(created_at=when))
        db.commit()
    db.refresh(order)
    return order


def check_in_first_tickets(db: Session, event: Event, staff: User, count: int) -> None:
    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.event_id == event.id, Ticket.status == "valid")
        .order_by(Ticket.created_at)
        .limit(count)
    ).all()
    for ticket in tickets:
        ticket_service.check_in_ticket(db, ticket, staff.id)


def assign_staff(db: Session, event: Event, staff: User) -> None:
    exists = db.scalar(
        select(StaffAssignment.id).where(
            StaffAssignment.event_id == event.id, StaffAssignment.user_id == staff.id
        )
    )
    if exists is None:
        db.add(
            StaffAssignment(
                event_id=event.id, user_id=staff.id, can_undo_check_in=True, can_manage_support=True
            )
        )
        db.commit()


def seed_paid_event(db: Session, demo: Demo) -> Event:
    """Paid event with completed activation, a promo campaign, staff and some sales."""
    organizer = demo.users["organizer"]
    event = find_event(db, EVENT_TITLE, organizer)
    if event is not None:
        return event

    event = create_event(
        db,
        demo,
        EVENT_TITLE,
        timedelta(days=14),
        "Live set by local bands. Seeded event for the demo.",
        "music",
        200,
        [("General admission", 5000 * KZT, 150), ("VIP", 15000 * KZT, 50)],
    )
    paid_sales_service.pay_fee(db, event, organizer.id, simulate_failure=False)
    paid_sales_service.accept_terms(db, event, organizer.id)
    paid_sales_service.activate(db, event, organizer.id)

    standard = ticket_type_named(db, event, "General admission")
    vip = ticket_type_named(db, event, "VIP")
    campaign = promo_service.create_campaign(
        db,
        event,
        PromoCampaignCreate(
            name="Instagram",
            discount_type="percent",
            discount_value=20,
            end_time=event.start_time,
            max_redemptions=50,
        ),
        organizer.id,
    )
    # A readable code for the demo; generated codes are random.
    if db.scalar(select(PromoCampaign.id).where(PromoCampaign.code == PROMO_CODE)) is None:
        campaign.code = PROMO_CODE
    db.commit()

    aigerim, daniyar, madina = demo.buyers
    place_order(db, event, aigerim, [(standard, 2)], days_ago=6)
    place_order(db, event, daniyar, [(vip, 1)], days_ago=4)
    place_order(db, event, madina, [(standard, 3)], days_ago=3, promo_code=campaign.code)
    place_order(db, event, aigerim, [(vip, 2)], days_ago=1, promo_code=campaign.code)
    place_order(db, event, demo.users["attendee"], [(standard, 1)])

    assign_staff(db, event, demo.users["event_admin"])
    return event


def seed_seated_event(db: Session, demo: Demo) -> Event:
    """Assigned-seating event in Main Hall with a few seats already sold (SRS 4.3.1)."""
    organizer = demo.users["organizer"]
    event = find_event(db, SEATED_EVENT_TITLE, organizer)
    if event is not None:
        return event

    event = create_event(
        db,
        demo,
        SEATED_EVENT_TITLE,
        timedelta(days=21),
        "Classical concert with assigned hall seating.",
        "music",
        MAIN_HALL.seat_count(),
        [],
        is_assigned_seating=True,
        venue=demo.main_hall,
    )
    paid_sales_service.pay_fee(db, event, organizer.id, simulate_failure=False)
    paid_sales_service.accept_terms(db, event, organizer.id)
    paid_sales_service.activate(db, event, organizer.id)

    lower = ticket_type_named(db, event, "Lower parterre")
    upper = ticket_type_named(db, event, "Upper parterre")
    balcony = ticket_type_named(db, event, "Balcony")

    aigerim, daniyar, madina = demo.buyers
    place_order(db, event, aigerim, [(lower, ["E-D-16", "E-D-17"])], days_ago=4)
    place_order(db, event, daniyar, [(balcony, ["BC-J-20"])], days_ago=2)
    place_order(db, event, madina, [(upper, ["B-S-21"])], days_ago=1)
    place_order(db, event, demo.users["attendee"], [(lower, ["E-C-15"])])

    assign_staff(db, event, demo.users["event_admin"])
    return event


def seed_free_event(db: Session, demo: Demo) -> Event:
    organizer = demo.users["organizer"]
    event = find_event(db, FREE_EVENT_TITLE, organizer)
    if event is not None:
        return event

    event = create_event(
        db,
        demo,
        FREE_EVENT_TITLE,
        timedelta(days=7),
        "Бесплатная лекция для студентов. Регистрация обязательна.",
        "education",
        100,
        [("Бесплатный вход", 0, 100)],
    )
    entry = ticket_type_named(db, event, "Бесплатный вход")
    for days_ago, buyer in zip((5, 3, 2), demo.buyers, strict=True):
        place_order(db, event, buyer, [(entry, 1)], days_ago=days_ago)
    assign_staff(db, event, demo.users["event_admin"])
    return event


def seed_past_event(db: Session, demo: Demo) -> Event:
    """A completed event with sales and check-ins for the history view (SRS 4.16)."""
    organizer = demo.users["organizer"]
    event = find_event(db, PAST_EVENT_TITLE, organizer)
    if event is not None:
        return event

    # Sell while the event is upcoming, then move it into the past.
    event = create_event(
        db,
        demo,
        PAST_EVENT_TITLE,
        timedelta(days=3),
        "An evening of jazz standards.",
        "music",
        80,
        [("Standard", 4000 * KZT, 80)],
    )
    paid_sales_service.pay_fee(db, event, organizer.id, simulate_failure=False)
    paid_sales_service.accept_terms(db, event, organizer.id)
    paid_sales_service.activate(db, event, organizer.id)
    standard = ticket_type_named(db, event, "Standard")
    for days_ago, buyer in zip((30, 26, 24), demo.buyers, strict=True):
        place_order(db, event, buyer, [(standard, 2)], days_ago=days_ago)

    assign_staff(db, event, demo.users["event_admin"])
    check_in_first_tickets(db, event, demo.users["event_admin"], count=4)

    start = time_now() - timedelta(days=20)
    event.start_time = start
    event.end_time = start + timedelta(hours=3)
    db.commit()
    return event


def seed_cancelled_event(db: Session, demo: Demo) -> Event:
    """A cancelled event whose paid orders were refunded."""
    organizer = demo.users["organizer"]
    event = find_event(db, CANCELLED_EVENT_TITLE, organizer)
    if event is not None:
        return event

    event = create_event(
        db,
        demo,
        CANCELLED_EVENT_TITLE,
        timedelta(days=10),
        "Open-air screening, cancelled because of the weather forecast.",
        "film",
        120,
        [("Standard", 2500 * KZT, 120)],
    )
    paid_sales_service.pay_fee(db, event, organizer.id, simulate_failure=False)
    paid_sales_service.accept_terms(db, event, organizer.id)
    paid_sales_service.activate(db, event, organizer.id)
    standard = ticket_type_named(db, event, "Standard")
    for days_ago, buyer in zip((9, 8), demo.buyers[:2], strict=True):
        place_order(db, event, buyer, [(standard, 1)], days_ago=days_ago)

    event_service.cancel_event(db, event, organizer.id)
    return event


SEED_STEPS: list[Callable[[Session, Demo], Event]] = [
    seed_paid_event,
    seed_seated_event,
    seed_free_event,
    seed_past_event,
    seed_cancelled_event,
]


def seed(db: Session) -> None:
    users = {role: seed_user(db, email, name, role) for email, name, role in USERS}
    buyers = [seed_user(db, email, name, "attendee") for email, name in BUYERS]
    seed_organizer_profile(db, users["organizer"])
    demo = Demo(users=users, buyers=buyers, venue=seed_venue(db), main_hall=seed_main_hall(db))
    for step in SEED_STEPS:
        step(db, demo)


def main() -> None:
    if not settings.IS_DEV_ENV:
        raise SystemExit("Refusing to seed: IS_DEV_ENV is false.")

    core.init_core()
    assert core.engine is not None
    with Session(core.engine) as db:
        seed(db)
    print("Seed complete.")
    print(f"  Sign in with any demo account and password {PASSWORD!r}:")
    for email, _, role in USERS:
        print(f"    {role:<15} {email}")
    print(f"  Promo code for {EVENT_TITLE!r}: {PROMO_CODE}")


if __name__ == "__main__":
    main()
