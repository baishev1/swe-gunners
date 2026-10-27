from datetime import timedelta

from sqlalchemy import select

import core
from core import *
from features.auth.service import hasher
from features.events.models import Event
from features.organizers.models import OrganizerProfile
from features.ticket_types.schemas import TicketTypeCreate
from features.ticket_types.service import ticket_type_service
from features.users.models import User
from features.venues.models import Venue

PASSWORD = "password123"

USERS = [
    ("attendee@biletflow.dev", "Demo Attendee", "attendee"),
    ("organizer@biletflow.dev", "Demo Organizer", "organizer"),
    ("eventadmin@biletflow.dev", "Demo Event Admin", "event_admin"),
    ("admin@biletflow.dev", "Demo Platform Admin", "platform_admin"),
]

EVENT_TITLE = "BiletFlow Demo Concert"


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
    profile = db.scalar(select(OrganizerProfile).where(OrganizerProfile.user_id == user.id))
    if profile is None:
        db.add(OrganizerProfile(user_id=user.id, organization_name="Demo Events LLP"))
        db.commit()


def seed_event(db: Session, organizer: User) -> Event:
    event = db.scalar(
        select(Event).where(Event.title == EVENT_TITLE, Event.organizer_id == organizer.id)
    )
    if event is not None:
        return event

    venue = db.scalar(select(Venue).where(Venue.name == "Demo Hall"))
    if venue is None:
        venue = Venue(name="Demo Hall", address="1 Abay Ave, Almaty")
        db.add(venue)
        db.flush()

    start = time_now() + timedelta(days=14)
    event = Event(
        title=EVENT_TITLE,
        description="Seeded event for local development.",
        category="music",
        venue_id=venue.id,
        start_time=start,
        end_time=start + timedelta(hours=3),
        capacity=200,
        visibility="public",
        status="published",
        organizer_id=organizer.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    ticket_type_service.create_ticket_type(
        db, event, TicketTypeCreate(name="General admission", price=5000, quantity=200)
    )
    return event


def seed(db: Session) -> None:
    users = {role: seed_user(db, email, name, role) for email, name, role in USERS}
    seed_organizer_profile(db, users["organizer"])
    seed_event(db, users["organizer"])


def main() -> None:
    if not settings.IS_DEV_ENV:
        raise SystemExit("Refusing to seed: IS_DEV_ENV is false.")

    core.init_core()
    assert core.engine is not None
    with Session(core.engine) as db:
        seed(db)
    print("Seed complete.")


if __name__ == "__main__":
    main()
