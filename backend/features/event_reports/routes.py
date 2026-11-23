from fastapi import APIRouter, Depends, status

from core import *
from features.auth.guards import get_current_user, require_role
from features.events.guards import valid_event_id
from features.events.models import Event
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import event_report_service

router = APIRouter(prefix="/event-reports", tags=["Event reports"])
admin_router = APIRouter(
    prefix="/admin/event-reports",
    tags=["Admin"],
    dependencies=[Depends(require_role("platform_admin"))],
)


@router.post("", response_model=EventReportResponse, status_code=status.HTTP_201_CREATED)
def report_event(
    data: EventReportCreate,
    event: Event = Depends(valid_event_id),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return event_report_service.create(db=db, event=event, data=data, reporter_id=user.id)


@admin_router.get("", response_model=list[EventReportResponse])
def list_reports(status: ReportStatus | None = None, db: Session = Depends(get_db)):
    return event_report_service.list_reports(db=db, status=status)


@admin_router.post("/review", response_model=EventReportResponse)
def review_report(
    report: EventReport = Depends(open_report_guard),
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return event_report_service.review(db=db, report=report, actor_id=admin.id)
