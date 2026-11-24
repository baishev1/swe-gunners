from fastapi import APIRouter, Depends, HTTPException, status

from core import *
from features.auth.guards import require_role
from features.events.guards import owned_event_guard, viewable_event_guard
from features.events.models import Event
from features.ticket_types.schemas import TicketTypeResponse
from features.ticket_types.service import ticket_type_service
from features.users.models import User

from .layouts import VenueLayout
from .schemas import *
from .service import seating_service

router = APIRouter(prefix="/seating", tags=["Seating"])


def event_layout(event: Event) -> VenueLayout:
    layout = seating_service.layout_for_event(event)
    if layout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This event's venue has no seating layout",
        )
    return layout


@router.get("/map", response_model=SeatMapResponse)
def get_seat_map(
    event: Event = Depends(viewable_event_guard),
    db: Session = Depends(get_db),
):
    if not event.is_assigned_seating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This event does not use assigned seating",
        )
    return seating_service.seat_map(db, event, event_layout(event))


@router.post("/setup", response_model=list[TicketTypeResponse])
def set_up_seating(
    data: SeatingSetupRequest,
    event: Event = Depends(owned_event_guard),
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    layout = event_layout(event)
    categories = [c.category for c in data.categories]
    known = {c.category for c in layout.categories}
    if len(set(categories)) != len(categories) or not set(categories) <= known:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each price category of the layout can appear only once",
        )
    ticket_types = seating_service.setup(db, event, layout, data, user.id)
    return ticket_type_service.attach_ticket_stats(db=db, ticket_types=ticket_types)
