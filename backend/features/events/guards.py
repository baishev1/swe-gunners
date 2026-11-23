import secrets

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.auth.guards import require_role
from features.users.dependencies import optional_user
from features.users.models import User
from features.venues.models import Venue

from .models import *
from .schemas import *


def valid_event_id(event_id: UUID, db: Session = Depends(get_db)) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def editable_event_guard(event: Event = Depends(valid_event_id)) -> Event:
    if event.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a cancelled event",
        )
    return event


def owned_event_guard(
    event: Event = Depends(editable_event_guard),
    user: User = Depends(require_role("organizer")),
) -> Event:
    if event.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def owned_event_id_guard(
    event: Event = Depends(valid_event_id),
    user: User = Depends(require_role("organizer")),
) -> Event:
    if event.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def is_event_manager(event: Event, user: User | None) -> bool:
    return user is not None and (user.id == event.organizer_id or user.role == "platform_admin")


def has_access_token(event: Event, access: str | None) -> bool:
    return bool(access and event.access_token) and secrets.compare_digest(
        access or "", event.access_token or ""
    )


def holds_order(db: Session, event: Event, user: User | None) -> bool:
    # Imported lazily: orders imports this module's models.
    from features.orders.models import Order

    if user is None:
        return False
    return (
        db.scalar(
            select(Order.id).where(Order.event_id == event.id, Order.user_id == user.id).limit(1)
        )
        is not None
    )


def can_view_event(
    event: Event, user: User | None, access: str | None = None, db: Session | None = None
) -> bool:
    """Public and unlisted events are open by link; private ones need the organizer's secret
    link, unless the user already has an order for the event (SRS 4.2)."""
    if is_event_manager(event, user):
        return True
    if event.status in ("draft", "unpublished", "suspended"):
        return False
    if event.visibility != "private":
        return True
    return has_access_token(event, access) or (db is not None and holds_order(db, event, user))


def viewable_event_guard(
    event_id: UUID,
    access: str | None = None,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> Event:
    event = db.get(Event, event_id)
    if event is None or not can_view_event(event, user, access, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def valid_event_create(data: EventCreate, db: Session = Depends(get_db)) -> EventCreate:
    if not db.get(Venue, data.venue_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )
    return data


def valid_event_update(data: EventUpdate, db: Session = Depends(get_db)) -> EventUpdate:
    if data.venue_id and not db.get(Venue, data.venue_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found",
        )
    return data
