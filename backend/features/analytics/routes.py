from fastapi import APIRouter, Depends
from pydantic import AwareDatetime

from core import *
from features.events.models import Event

from .guards import *
from .schemas import *
from .service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/event", response_model=EventAnalyticsResponse)
def get_event_analytics(
    event: Event = Depends(managed_event_guard),
    date_range: tuple[AwareDatetime | None, AwareDatetime | None] = Depends(valid_date_range),
    ticket_type_id: UUID | None = Depends(event_ticket_type_filter),
    db: Session = Depends(get_db),
):
    date_from, date_to = date_range
    return analytics_service.event_analytics(
        db=db,
        event=event,
        date_from=date_from,
        date_to=date_to,
        ticket_type_id=ticket_type_id,
    )
