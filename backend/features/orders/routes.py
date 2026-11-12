from fastapi import APIRouter, Depends, status

from core import *
from features.auth.guards import get_current_user
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate = Depends(paid_sales_open_order_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.create_order(db=db, data=data, user_id=user.id)


@router.get("", response_model=list[OrderResponse])
def list_orders(
    event_id: UUID | None = None,
    status: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.list_orders(db=db, user_id=user.id, event_id=event_id, status=status)


@router.get("/detail", response_model=OrderResponse)
def get_order_detail(order: Order = Depends(accessible_order_guard)):
    return order


@router.post("/cancel", response_model=OrderResponse)
def cancel_order(
    order: Order = Depends(cancellable_order_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return order_service.cancel_order(db=db, order=order, actor_id=user.id)
