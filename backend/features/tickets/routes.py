from fastapi import APIRouter, Depends

from core import *
from features.users.dependencies import active_user
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("", response_model=list[TicketResponse])
def list_tickets(
    order_id: UUID | None = None,
    event_id: UUID | None = None,
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    return ticket_service.list_tickets(db=db, user_id=user.id, order_id=order_id, event_id=event_id)


@router.get("/detail", response_model=TicketResponse)
def get_ticket_detail(ticket: Ticket = Depends(accessible_ticket_guard)):
    return ticket


@router.get("/verify", response_model=TicketVerificationResponse)
def verify_ticket(scan: tuple[Ticket | None, str] = Depends(scanned_ticket_status)):
    ticket, ticket_status = scan
    return TicketVerificationResponse(
        valid=ticket_status == "valid",
        status=ticket_status,
        ticket=TicketResponse.model_validate(ticket) if ticket is not None else None,
        message="Ticket is valid" if ticket_status == "valid" else f"Ticket is {ticket_status}",
    )


@router.post("/check-in", response_model=TicketResponse)
def check_in_ticket(
    ticket: Ticket = Depends(scanner_ticket),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    return ticket_service.check_in_ticket(db=db, ticket=ticket, actor_id=user.id)


@router.post("/undo-check-in", response_model=TicketResponse)
def undo_check_in(
    ticket: Ticket = Depends(reversible_scanner_ticket),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    return ticket_service.undo_check_in(db=db, ticket=ticket, actor_id=user.id)


@router.get("/pdf")
def download_ticket_pdf(
    ticket: Ticket = Depends(accessible_ticket_guard),
    db: Session = Depends(get_db),
):
    pdf_bytes = ticket_service.generate_pdf_ticket(db=db, ticket=ticket)
    from fastapi.responses import Response

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ticket-{ticket.id}.pdf"'},
    )
