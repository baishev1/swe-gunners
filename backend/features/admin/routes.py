from fastapi import APIRouter, Depends

from core import *
from features.auth.guards import get_current_user, require_role
from features.events.models import Event
from features.events.schemas import EventResponse
from features.paid_sales.guards import (
    reinstatable_activation_guard,
    suspendable_activation_guard,
)
from features.paid_sales.models import PaidSalesActivation
from features.paid_sales.schemas import PaidSalesActivationResponse, PaidSalesSuspendRequest
from features.paid_sales.service import paid_sales_service
from features.promo.schemas import PromoCampaignResponse
from features.users.models import User

from .guards import *
from .schemas import *
from .service import admin_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("platform_admin"))],
)


@router.get("/users", response_model=list[AdminUserResponse])
def search_users(q: str | None = None, role: str | None = None, db: Session = Depends(get_db)):
    return admin_service.search_users(db=db, q=q, role=role)


@router.post("/users/suspend", response_model=AdminUserResponse)
def suspend_user(
    target: User = Depends(suspendable_user_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return admin_service.suspend_user(db=db, user=target, actor_id=admin.id)


@router.get("/events", response_model=list[EventResponse])
def search_events(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    return admin_service.search_events(db=db, q=q, status=status)


@router.post("/events/suspend", response_model=EventResponse)
def suspend_event(
    event: Event = Depends(suspendable_event_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return admin_service.suspend_event(db=db, event=event, actor_id=admin.id)


@router.get("/paid-sales", response_model=list[PaidSalesActivationResponse])
def list_paid_sales_activations(status: str | None = None, db: Session = Depends(get_db)):
    return paid_sales_service.list_activations(db=db, status=status)


@router.post("/paid-sales/suspend", response_model=PaidSalesActivationResponse)
def suspend_paid_sales(
    data: PaidSalesSuspendRequest,
    activation: PaidSalesActivation = Depends(suspendable_activation_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return paid_sales_service.suspend(
        db=db, activation=activation, reason=data.reason, actor_id=admin.id
    )


@router.post("/paid-sales/reinstate", response_model=PaidSalesActivationResponse)
def reinstate_paid_sales(
    activation: PaidSalesActivation = Depends(reinstatable_activation_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return paid_sales_service.reinstate(db=db, activation=activation, actor_id=admin.id)


@router.get("/promo-campaigns", response_model=list[PromoCampaignResponse])
def search_campaigns(q: str | None = None, db: Session = Depends(get_db)):
    return admin_service.search_campaigns(db=db, q=q)


@router.get("/settings", response_model=PlatformSettingResponse)
def get_settings(db: Session = Depends(get_db)):
    return admin_service.get_settings(db=db)


@router.patch("/settings", response_model=PlatformSettingResponse)
def update_settings(
    data: PlatformSettingUpdate,
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return admin_service.update_settings(db=db, data=data, actor_id=admin.id)
