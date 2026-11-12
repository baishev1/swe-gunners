from fastapi import APIRouter, Depends, status

from core import *

from .guards import *
from .models import *
from .schemas import *
from .service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate = Depends(paid_sales_open_order_guard),
    db: Session = Depends(get_db),
):
    return order_service.create_order(db=db, data=data)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    user_id: UUID | None = None,
    event_id: UUID | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return order_service.list_orders(db=db, user_id=user_id, event_id=event_id, status=status)


@router.get("/detail", response_model=OrderResponse)
def get_order_detail(order: Order = Depends(valid_order_id)):
    return order


@router.post("/cancel", response_model=OrderResponse)
def cancel_order(
    order: Order = Depends(cancellable_order_guard),
    db: Session = Depends(get_db),
):
    return order_service.cancel_order(db=db, order=order)
