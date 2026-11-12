from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime

from core import *
from features.auth.guards import get_current_user, require_role
from features.events.models import Event
from features.events.schemas import EventResponse
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


@router.get("/orders", response_model=list[AdminOrderResponse])
def search_orders(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    return admin_service.search_orders(db=db, q=q, status=status)


@router.get("/payments", response_model=list[AdminPaymentResponse])
def search_payments(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    return admin_service.search_payments(db=db, q=q, status=status)


@router.get("/monitoring", response_model=AdminMonitoringResponse)
def get_monitoring(db: Session = Depends(get_db)):
    return admin_service.monitoring(db=db)


@router.get("/reports/export", response_class=Response)
def export_report(
    report: ReportKind = Query(),
    date_from: AwareDatetime | None = None,
    date_to: AwareDatetime | None = None,
    db: Session = Depends(get_db),
):
    content = admin_service.export_report(
        db=db, report=report, date_from=date_from, date_to=date_to
    )
    filename = f"biletflow-{report}-{time_now():%Y%m%d}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
