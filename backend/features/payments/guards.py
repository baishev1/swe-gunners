from fastapi import Depends, HTTPException, status

from core import *
from features.orders.models import Order
from features.paid_sales.service import paid_sales_service

from .models import *
from .schemas import *


def payable_order_guard(data: PaymentSimulateRequest, db: Session = Depends(get_db)) -> Order:
    order = db.get(Order, data.order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be paid with status '{order.status}'",
        )
    if order.total_amount_kzt > 0 and not paid_sales_service.is_open(db, order.event_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid ticket sales are not active for this event",
        )
    return order
