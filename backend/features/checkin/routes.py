from fastapi import APIRouter, Depends, Query, status

from core import *
from features.events.models import Event
from features.events.schemas import EventResponse
from features.tickets.schemas import EventAttendeeResponse
from features.users.dependencies import active_user
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import checkin_service

router = APIRouter(prefix="/checkin", tags=["Check-in"])


@router.get("/events", response_model=list[AssignedEventResponse])
def list_assigned_events(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    events = checkin_service.list_events(db, user, limit, offset)
    undoable = checkin_service.undoable_event_ids(db, user, events)
    return [
        AssignedEventResponse(
            **EventResponse.model_validate(event).model_dump(),
            can_undo_check_in=event.id in undoable,
        )
        for event in events
    ]


@router.get("/attendees", response_model=list[EventAttendeeResponse])
def search_attendees(
    q: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    event: Event = Depends(assigned_event),
    db: Session = Depends(get_db),
):
    return [
        EventAttendeeResponse(
            ticket_id=ticket.id,
            order_id=ticket.order_id,
            attendee_name=ticket.attendee_name,
            attendee_email=ticket.attendee_email,
            ticket_type_id=ticket.ticket_type_id,
            ticket_type_name=ticket.ticket_type_name,
            ticket_status=ticket.status,
            order_status=order_status,
            checked_in_at=ticket.checked_in_at,
            created_at=ticket.created_at,
        )
        for ticket, order_status in checkin_service.search_attendees(db, event, q, limit, offset)
    ]


@router.get("/summary", response_model=CheckInSummaryResponse)
def get_summary(event: Event = Depends(assigned_event), db: Session = Depends(get_db)):
    registered, checked_in = checkin_service.summary(db, event)
    return CheckInSummaryResponse(event_id=event.id, registered=registered, checked_in=checked_in)


@router.post("/staff", response_model=StaffAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_staff(
    data: StaffAssignmentCreate = Depends(valid_staff_assignment),
    event: Event = Depends(managed_event),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    return checkin_service.assign_staff(db, event, data, user.id)


@router.get("/staff", response_model=list[StaffAssignmentResponse])
def list_staff(
    event: Event = Depends(managed_event),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return checkin_service.list_staff(db, event, limit, offset)


@router.delete("/staff", status_code=status.HTTP_204_NO_CONTENT)
def revoke_staff(
    assignment: StaffAssignment = Depends(managed_assignment),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    checkin_service.revoke_staff(db, assignment, user.id)
