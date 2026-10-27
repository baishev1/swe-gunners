from fastapi import APIRouter, Depends
from pydantic import AwareDatetime

from core import *
from features.events.models import Event

from .guards import *
from .schemas import *
from .service import audit_log_service

router = APIRouter(prefix="/audit-log", tags=["Audit log"])


@router.get("/timeline", response_model=list[AuditLogResponse])
def get_event_timeline(
    date_from: AwareDatetime | None = None,
    date_to: AwareDatetime | None = None,
    action: str | None = None,
    event: Event = Depends(event_history_guard),
    db: Session = Depends(get_db),
):
    return audit_log_service.list_event_entries(
        db=db, event_id=event.id, date_from=date_from, date_to=date_to, action=action
    )
