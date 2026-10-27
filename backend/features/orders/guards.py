from fastapi import Depends, HTTPException, status

from core import *

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
