from fastapi import Depends, HTTPException, status

from core import *
from features.auth.guards import require_role
from features.events.guards import can_view_event, is_event_manager, owned_event_guard
from features.users.dependencies import optional_user
from features.users.models import User

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


def valid_ticket_type_id(ticket_type_id: UUID, db: Session = Depends(get_db)) -> TicketType:
    ticket_type = db.get(TicketType, ticket_type_id)
    if not ticket_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )
    return ticket_type


def viewable_ticket_types_event(
    event_id: UUID,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> Event:
    event = db.get(Event, event_id)
    if event is None or not can_view_event(event, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def viewable_ticket_type_guard(
    ticket_type: TicketType = Depends(valid_ticket_type_id),
    user: User | None = Depends(optional_user),
) -> TicketType:
    if not can_view_event(ticket_type.event, user) or (
        ticket_type.is_hidden and not is_event_manager(ticket_type.event, user)
    ):
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


def owned_ticket_type_guard(
    ticket_type: TicketType = Depends(editable_ticket_type_guard),
    user: User = Depends(require_role("organizer")),
) -> TicketType:
    if ticket_type.event.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )
    return ticket_type


def valid_ticket_type_create(
    data: TicketTypeCreate,
    event: Event = Depends(owned_event_guard),
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
    ticket_type: TicketType = Depends(owned_ticket_type_guard),
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
