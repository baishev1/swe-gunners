from fastapi import APIRouter, Depends, HTTPException, status

from core import *
from features.auth.guards import get_current_user
from features.events.guards import owned_event_id_guard
from features.events.models import Event
from features.users.models import User

from .guards import *
from .schemas import *
from .service import paid_sales_service

router = APIRouter(prefix="/paid-sales", tags=["Paid sales"])


@router.get("/checklist", response_model=PaidSalesChecklistResponse)
def get_checklist(
    event: Event = Depends(owned_event_id_guard),
    db: Session = Depends(get_db),
):
    return paid_sales_service.build_checklist(db=db, event=event)


@router.post("/pay-fee", response_model=PaidSalesChecklistResponse)
def pay_activation_fee(
    data: ActivationFeePaymentRequest,
    event: Event = Depends(pending_activation_event_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paid_sales_service.pay_fee(
        db=db, event=event, actor_id=user.id, simulate_failure=data.simulate_failure
    )
    if data.simulate_failure:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Simulated activation fee payment failed",
        )
    return paid_sales_service.build_checklist(db=db, event=event)


@router.post("/accept-terms", response_model=PaidSalesChecklistResponse)
def accept_paid_event_terms(
    event: Event = Depends(pending_activation_event_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paid_sales_service.accept_terms(db=db, event=event, actor_id=user.id)
    return paid_sales_service.build_checklist(db=db, event=event)


@router.post("/activate", response_model=PaidSalesChecklistResponse)
def activate_paid_sales(
    event: Event = Depends(activatable_event_guard),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paid_sales_service.activate(db=db, event=event, actor_id=user.id)
    return paid_sales_service.build_checklist(db=db, event=event)
