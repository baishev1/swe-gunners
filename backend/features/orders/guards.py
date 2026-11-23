from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.auth.guards import get_current_user
from features.events.guards import can_view_event
from features.events.models import Event
from features.paid_sales.service import paid_sales_service
from features.promo.service import promo_service
from features.ticket_types.models import TicketType
from features.users.models import User

from .models import *
from .schemas import *


def valid_order_id(order_id: UUID, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


def can_access_order(db: Session, order: Order, user: User) -> bool:
    if order.user_id == user.id or user.role == "platform_admin":
        return True
    event = db.get(Event, order.event_id)
    return event is not None and event.organizer_id == user.id


def accessible_order_guard(
    order: Order = Depends(valid_order_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    if not can_access_order(db, order, user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order


def cancellable_order_guard(
    order: Order = Depends(accessible_order_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    if order.status not in ("pending", "paid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an order with status '{order.status}'",
        )
    if order.status == "paid":
        # Paid cancellations refund tickets back to inventory (SRS 4.9), so only
        # the organizer or a platform admin may run them — never the buyer.
        event = db.get(Event, order.event_id)
        if user.role != "platform_admin" and (event is None or event.organizer_id != user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organizer can cancel a paid order",
            )
    return order


def refundable_order_guard(
    order: Order = Depends(valid_order_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    event = db.get(Event, order.event_id)
    if event is None or (user.role != "platform_admin" and event.organizer_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund an order with status '{order.status}'",
        )
    return order


def valid_order_create(
    data: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderCreate:
    event = db.get(Event, data.event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if event.status != "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not open for registration",
        )
    # A private event sells only through its secret link (SRS 4.2).
    if not can_view_event(event, user, data.access_token, db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    now = time_now()
    if event.registration_start_time and now < event.registration_start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration has not opened yet",
        )
    if event.registration_end_time and now > event.registration_end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is closed",
        )

    ticket_type_ids = [item.ticket_type_id for item in data.items]
    if len(set(ticket_type_ids)) != len(ticket_type_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each ticket type can appear only once per order",
        )
    ticket_types = {
        t.id: t
        for t in db.scalars(
            select(TicketType).where(
                TicketType.id.in_(ticket_type_ids),
                TicketType.event_id == event.id,
                TicketType.is_hidden.is_(False),
            )
        )
    }

    for item in data.items:
        ticket_type = ticket_types.get(item.ticket_type_id)
        if ticket_type is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ticket type not found"
            )
        if (ticket_type.sales_start_time and now < ticket_type.sales_start_time) or (
            ticket_type.sales_end_time and now > ticket_type.sales_end_time
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{ticket_type.name} is not on sale",
            )
        if ticket_type.max_per_order and item.quantity > ticket_type.max_per_order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"At most {ticket_type.max_per_order} {ticket_type.name} tickets per order",
            )

    if data.promo_code:
        campaign = promo_service.find_by_code(db, event.id, data.promo_code)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is not valid"
            )
        error = promo_service.redeem_error(campaign)
        if error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
        if not any(promo_service.applies_to(campaign, item.ticket_type_id) for item in data.items):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promo code does not apply to the selected tickets",
            )
    return data


def paid_sales_open_order_guard(
    data: OrderCreate = Depends(valid_order_create), db: Session = Depends(get_db)
) -> OrderCreate:
    """Rejects paid items unless the event passed Paid Sales Activation (SRS 4.5)."""
    ticket_type_ids = [item.ticket_type_id for item in data.items]
    has_paid_type = (
        db.scalar(
            select(TicketType.id)
            .where(TicketType.id.in_(ticket_type_ids), TicketType.price > 0)
            .limit(1)
        )
        is not None
    )
    if has_paid_type and not paid_sales_service.is_open(db, data.event_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid ticket sales are not active for this event",
        )
    return data
