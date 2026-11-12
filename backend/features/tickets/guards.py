import re

from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.auth.guards import get_current_user
from features.checkin.guards import assigned_event, undo_check_in_event
from features.events.models import Event
from features.orders.guards import can_access_order
from features.orders.models import Order
from features.users.models import User

from .models import *
from .schemas import *


def valid_ticket_id(ticket_id: UUID, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


def accessible_ticket_guard(
    ticket: Ticket = Depends(valid_ticket_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Ticket:
    order = db.get(Order, ticket.order_id)
    if order is None or not can_access_order(db, order, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


def scanner_ticket(
    ticket_id: UUID,
    event: Event = Depends(assigned_event),
    db: Session = Depends(get_db),
) -> Ticket:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.event_id == event.id))
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found for this event")
    return ticket


def reversible_scanner_ticket(
    event: Event = Depends(undo_check_in_event),
    ticket: Ticket = Depends(scanner_ticket),
) -> Ticket:
    return ticket


def scanned_ticket_status(
    qr_token: str,
    event: Event = Depends(assigned_event),
    db: Session = Depends(get_db),
) -> tuple[Ticket | None, str]:
    # Only resolve canonical admission tokens, never campaign links or campaign tokens.
    if re.fullmatch(r"[0-9a-f]{64}", qr_token) is None:
        return None, "not_found"
    ticket = db.scalar(
        select(Ticket).where(
            Ticket.qr_token == qr_token,
            Ticket.event_id == event.id,
        )
    )
    if ticket is None:
        return None, "not_found"
    order = db.get(Order, ticket.order_id)
    if order is None or order.event_id != event.id:
        return ticket, "invalid_order"
    if order.status != "paid":
        return ticket, order.status
    return ticket, ticket.status
