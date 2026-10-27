from fastapi import Depends, HTTPException, status

from core import *

from .models import *
from .schemas import *
from .service import ticket_type_service


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


def valid_ticket_type_id(ticket_type_id: UUID, db: Session = Depends(get_db)) -> TicketType:
    ticket_type = db.get(TicketType, ticket_type_id)
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )
    return ticket_type


def editable_ticket_type_guard(
    ticket_type: TicketType = Depends(valid_ticket_type_id),
) -> TicketType:
    if ticket_type.event.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a cancelled event",
        )
    return ticket_type


def valid_ticket_type_create(
    data: TicketTypeCreate,
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
) -> TicketTypeCreate:
    if ticket_type_service.total_quantity(db, event.id) + data.quantity > event.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket quantity exceeds event capacity",
        )
    return data


def valid_ticket_type_update(
    data: TicketTypeUpdate,
    ticket_type: TicketType = Depends(editable_ticket_type_guard),
    db: Session = Depends(get_db),
) -> TicketTypeUpdate:
    if data.quantity is None:
        return data
    if data.quantity < ticket_type.reserved_count + ticket_type.sold_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity is lower than tickets already reserved or sold",
        )
    others = ticket_type_service.total_quantity(db, ticket_type.event_id, ticket_type.id)
    if others + data.quantity > ticket_type.event.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket quantity exceeds event capacity",
        )
    return data
