from fastapi import APIRouter, Depends

from core import *
from features.orders.models import Order

from .guards import *
from .models import *
from .schemas import *
from .service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/simulate", response_model=PaymentResponse)
def simulate_payment(
    data: PaymentSimulateRequest,
    order: Order = Depends(payable_order_guard),
    db: Session = Depends(get_db),
):
    return payment_service.process_simulation(
        db=db, order=order, simulate_failure=data.simulate_failure
    )


@router.get("/detail", response_model=PaymentResponse)
def get_payment_detail(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    payment = payment_service.get_payment_by_order(db=db, order_id=order_id)
    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found for order",
        )
    return payment
