from fastapi import APIRouter, Depends, HTTPException, status

from core import *
from features.auth.guards import get_current_user, require_role
from features.events.guards import owned_event_id_guard
from features.events.models import Event
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import paid_sales_service

router = APIRouter(prefix="/paid-sales", tags=["Paid sales"])
# Lives here rather than in features/admin so admin never imports this feature,
# which imports admin for the activation fee.
admin_router = APIRouter(
    prefix="/admin/paid-sales",
    tags=["Admin"],
    dependencies=[Depends(require_role("platform_admin"))],
)


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


@admin_router.get("", response_model=list[PaidSalesActivationResponse])
def list_paid_sales_activations(status: str | None = None, db: Session = Depends(get_db)):
    return paid_sales_service.list_activations(db=db, status=status)


@admin_router.post("/suspend", response_model=PaidSalesActivationResponse)
def suspend_paid_sales(
    data: PaidSalesSuspendRequest,
    activation: PaidSalesActivation = Depends(suspendable_activation_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return paid_sales_service.suspend(
        db=db, activation=activation, reason=data.reason, actor_id=admin.id
    )


@admin_router.post("/reinstate", response_model=PaidSalesActivationResponse)
def reinstate_paid_sales(
    activation: PaidSalesActivation = Depends(reinstatable_activation_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return paid_sales_service.reinstate(db=db, activation=activation, actor_id=admin.id)
