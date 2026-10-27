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
    return ticket_type_service.create_ticket_type(db=db, event=event, data=data)


@router.get("", response_model=list[TicketTypeResponse])
def list_ticket_types(
    include_hidden: bool = False,
    event: Event = Depends(valid_event_id),
    db: Session = Depends(get_db),
):
    return ticket_type_service.list_ticket_types(
        db=db, event_id=event.id, include_hidden=include_hidden
    )


@router.get("/detail", response_model=TicketTypeResponse)
def get_ticket_type_detail(ticket_type: TicketType = Depends(valid_ticket_type_id)):
    return ticket_type


@router.patch("/update", response_model=TicketTypeResponse)
def update_ticket_type(
    data: TicketTypeUpdate = Depends(valid_ticket_type_update),
    ticket_type: TicketType = Depends(owned_ticket_type_guard),
    db: Session = Depends(get_db),
):
    return ticket_type_service.update_ticket_type(db=db, ticket_type=ticket_type, data=data)
