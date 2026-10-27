from fastapi import APIRouter, Depends

from core import *

from .guards import *
from .models import *
from .schemas import *
from .service import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    order_id: UUID | None = None,
    event_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return ticket_service.list_tickets(db=db, order_id=order_id, event_id=event_id)


@router.get("/detail", response_model=TicketResponse)
def get_ticket_detail(ticket: Ticket = Depends(valid_ticket_id)):
    return ticket


@router.get("/verify", response_model=TicketVerificationResponse)
def verify_ticket(qr_token: str, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket_by_qr_token(db=db, qr_token=qr_token)
    if not ticket:
        return TicketVerificationResponse(
            valid=False,
            status="not_found",
            ticket=None,
            message="Ticket not found",
        )
    if ticket.status != "valid":
        return TicketVerificationResponse(
            valid=False,
            status=ticket.status,
            ticket=TicketResponse.model_validate(ticket),
            message=f"Ticket is {ticket.status}",
        )
    return TicketVerificationResponse(
        valid=True,
        status="valid",
        ticket=TicketResponse.model_validate(ticket),
        message="Ticket is valid",
    )


@router.post("/check-in", response_model=TicketResponse)
def check_in_ticket(
    ticket: Ticket = Depends(valid_ticket_id),
    db: Session = Depends(get_db),
):
    return ticket_service.check_in_ticket(db=db, ticket=ticket)


@router.post("/undo-check-in", response_model=TicketResponse)
def undo_check_in(
    ticket: Ticket = Depends(valid_ticket_id),
    db: Session = Depends(get_db),
):
    return ticket_service.undo_check_in(db=db, ticket=ticket)


@router.get("/pdf")
def download_ticket_pdf(
    ticket: Ticket = Depends(valid_ticket_id),
    db: Session = Depends(get_db),
):
    pdf_bytes = ticket_service.generate_pdf_ticket(db=db, ticket=ticket)
    from fastapi.responses import Response

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ticket-{ticket.id}.pdf"'},
    )
