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
def get_payment_detail(payment: Payment = Depends(order_payment_guard)):
    return payment
