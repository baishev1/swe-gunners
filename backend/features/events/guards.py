from fastapi import Depends, HTTPException, status

from core import *
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
