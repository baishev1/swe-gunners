from fastapi import APIRouter, Depends, status

from core import *

from .guards import *
from .models import *
from .schemas import *
from .service import ticket_type_service

router = APIRouter(prefix="/ticket-types", tags=["Ticket Types"])


@router.post("", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(
    data: TicketTypeCreate = Depends(valid_ticket_type_create),
    event: Event = Depends(owned_event_guard),
    db: Session = Depends(get_db),
):
    ticket_type = ticket_type_service.create_ticket_type(db=db, event=event, data=data)
    return ticket_type_service.attach_ticket_stats(db=db, ticket_types=[ticket_type])[0]


@router.get("", response_model=list[TicketTypeResponse])
def list_ticket_types(
    include_hidden: bool = False,
    event: Event = Depends(viewable_ticket_types_event),
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    return ticket_type_service.attach_ticket_stats(
        db=db,
        ticket_types=ticket_type_service.list_ticket_types(
            db=db,
            event_id=event.id,
            include_hidden=include_hidden and is_event_manager(event, user),
        ),
    )


@router.get("/detail", response_model=TicketTypeResponse)
def get_ticket_type_detail(
    ticket_type: TicketType = Depends(viewable_ticket_type_guard),
    db: Session = Depends(get_db),
):
    return ticket_type_service.attach_ticket_stats(db=db, ticket_types=[ticket_type])[0]


@router.patch("/update", response_model=TicketTypeResponse)
def update_ticket_type(
    data: TicketTypeUpdate = Depends(valid_ticket_type_update),
    ticket_type: TicketType = Depends(owned_ticket_type_guard),
    db: Session = Depends(get_db),
):
    updated = ticket_type_service.update_ticket_type(db=db, ticket_type=ticket_type, data=data)
    return ticket_type_service.attach_ticket_stats(db=db, ticket_types=[updated])[0]
