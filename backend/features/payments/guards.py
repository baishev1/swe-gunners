from fastapi import Depends, HTTPException, status

from core import *
from features.auth.guards import get_current_user
from features.orders.guards import accessible_order_guard
from features.orders.models import Order
from features.paid_sales.service import paid_sales_service
from features.users.models import User

from .models import *
from .schemas import *
from .service import payment_service


def payable_order_guard(
    data: PaymentSimulateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    order = db.get(Order, data.order_id)
    if not order or order.user_id != user.id:
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


def order_payment_guard(
    order: Order = Depends(accessible_order_guard), db: Session = Depends(get_db)
) -> Payment:
    payment = payment_service.get_payment_by_order(db=db, order_id=order.id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found for order",
        )
    return payment
