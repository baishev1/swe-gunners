from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.paid_sales.service import paid_sales_service
from features.ticket_types.models import TicketType

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


def cancellable_order_guard(order: Order = Depends(valid_order_id)) -> Order:
    if order.status not in ("pending", "paid"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an order with status '{order.status}'",
        )
    return order


def paid_sales_open_order_guard(data: OrderCreate, db: Session = Depends(get_db)) -> OrderCreate:
    """Rejects paid items unless the event passed Paid Sales Activation (SRS 4.5).

    Stored ticket prices are checked too, so a client cannot dodge the rule by
    sending a zero price for a paid ticket type.
    """
    ticket_type_ids = [item.ticket_type_id for item in data.items]
    has_stored_paid_type = (
        db.scalar(
            select(TicketType.id)
            .where(TicketType.id.in_(ticket_type_ids), TicketType.price > 0)
            .limit(1)
        )
        is not None
    )
    has_paid_item = any(item.unit_price_kzt > 0 for item in data.items)
    if (has_paid_item or has_stored_paid_type) and not paid_sales_service.is_open(
        db, data.event_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid ticket sales are not active for this event",
        )
    return data
