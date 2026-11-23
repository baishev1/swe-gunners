from fastapi import Depends, HTTPException
from sqlalchemy import select

from core import *
from features.checkin.models import StaffAssignment
from features.events.guards import can_view_event, holds_order
from features.events.models import Event
from features.orders.guards import can_access_order
from features.orders.models import Order
from features.tickets.models import Ticket
from features.users.models import User

from .dependencies import active_support_user
from .models import *
from .schemas import *


def valid_support_create(
    data: SupportCaseCreate,
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCaseCreate:
    if data.target == "platform" and user.role not in {"organizer", "platform_admin"}:
        raise HTTPException(status_code=403, detail="Platform support is for organizers")
    data = attach_order_context(db, data, user)
    if data.event_id is not None:
        event = db.get(Event, data.event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        owns_event = event.organizer_id == user.id
        if data.target == "platform" and not owns_event and user.role != "platform_admin":
            raise HTTPException(status_code=403, detail="Event access denied")
        # Anyone who can see the event, or already holds an order for it, may ask its
        # organizer; that includes attendees of private and cancelled events.
        if data.target == "organizer" and not (
            can_view_event(event, user, db=db) or holds_order(db, event, user)
        ):
            raise HTTPException(status_code=404, detail="Event not found")
    return data


def attach_order_context(db: Session, data: SupportCaseCreate, user: User) -> SupportCaseCreate:
    """Checks the order or ticket belongs to the requester and fills in the event (SRS 4.13)."""
    if data.ticket_id is None and data.order_id is None:
        return data
    ticket = db.get(Ticket, data.ticket_id) if data.ticket_id else None
    if data.ticket_id and ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    order_id = ticket.order_id if ticket else data.order_id
    if data.order_id and order_id != data.order_id:
        raise HTTPException(status_code=400, detail="The ticket is not part of this order")
    order = db.get(Order, order_id)
    if order is None or not can_access_order(db, order, user):
        raise HTTPException(status_code=404, detail="Order not found")
    if data.event_id and data.event_id != order.event_id:
        raise HTTPException(status_code=400, detail="The order is for a different event")
    return data.model_copy(update={"order_id": order.id, "event_id": order.event_id})


def support_case_staff(db: Session, case: SupportCase, user: User) -> bool:
    if user.role == "platform_admin":
        return True
    if case.target == "organizer" and case.event_id is not None:
        event = db.get(Event, case.event_id)
        if event is not None and event.organizer_id == user.id:
            return True
        return (
            db.scalar(
                select(StaffAssignment.id).where(
                    StaffAssignment.event_id == case.event_id,
                    StaffAssignment.user_id == user.id,
                    StaffAssignment.can_manage_support.is_(True),
                )
            )
            is not None
        )
    return False


def accessible_support_case(
    case_id: UUID,
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCase:
    case = db.get(SupportCase, case_id)
    if case is None or (case.requester_id != user.id and not support_case_staff(db, case, user)):
        raise HTTPException(status_code=404, detail="Support case not found")
    return case


def managed_support_case(
    case: SupportCase = Depends(accessible_support_case),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCase:
    if not support_case_staff(db, case, user):
        raise HTTPException(status_code=403, detail="Only support staff can manage this case")
    return case
