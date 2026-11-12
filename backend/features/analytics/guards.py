from fastapi import Depends, HTTPException, status
from pydantic import AwareDatetime

from core import *
from features.audit_log.guards import event_history_guard
from features.events.models import Event
from features.ticket_types.models import TicketType


def managed_event_guard(event: Event = Depends(event_history_guard)) -> Event:
    """Organizers see analytics only for their own events; platform admins see all."""
    return event


def valid_date_range(
    date_from: AwareDatetime | None = None,
    date_to: AwareDatetime | None = None,
) -> tuple[AwareDatetime | None, AwareDatetime | None]:
    if date_from and date_to and date_from >= date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from must be earlier than date_to",
        )
    return date_from, date_to


def event_ticket_type_filter(
    ticket_type_id: UUID | None = None,
    event: Event = Depends(managed_event_guard),
    db: Session = Depends(get_db),
) -> UUID | None:
    if ticket_type_id is None:
        return None
    ticket_type = db.get(TicketType, ticket_type_id)
    if ticket_type is None or ticket_type.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket type not found",
        )
    return ticket_type_id
