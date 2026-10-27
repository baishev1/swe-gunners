import secrets

from sqlalchemy import select

from core import *
from features.orders.models import Order

from .models import *
from .schemas import *


class TicketService:
    def generate_qr_token(self) -> str:
        return secrets.token_hex(32)

    def issue_tickets_for_order(self, db: Session, order: Order) -> list[Ticket]:
        tickets: list[Ticket] = []
        for item in order.items:
            for _ in range(item.quantity):
                ticket = Ticket(
                    order_id=order.id,
                    order_item_id=item.id,
                    event_id=order.event_id,
                    ticket_type_id=item.ticket_type_id,
                    ticket_type_name=item.ticket_type_name,
                    attendee_name=order.customer_name,
                    attendee_email=order.customer_email,
                    qr_token=self.generate_qr_token(),
                    status="valid",
                )
                db.add(ticket)
                tickets.append(ticket)

        db.commit()
        for t in tickets:
            db.refresh(t)
        return tickets

    def list_tickets(
        self,
        db: Session,
        order_id: UUID | None = None,
        event_id: UUID | None = None,
    ) -> list[Ticket]:
        stmt = select(Ticket)
        if order_id:
            stmt = stmt.where(Ticket.order_id == order_id)
        if event_id:
            stmt = stmt.where(Ticket.event_id == event_id)
        stmt = stmt.order_by(Ticket.created_at.asc())
        return list(db.scalars(stmt).all())

    def get_ticket_by_qr_token(self, db: Session, qr_token: str) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.qr_token == qr_token)
        return db.scalar(stmt)

    def check_in_ticket(self, db: Session, ticket: Ticket) -> Ticket:
        if ticket.status == "checked_in":
            raise HTTPException(
                status_code=400,
                detail="Ticket is already checked in",
            )
        if ticket.status != "valid":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot check in ticket with status '{ticket.status}'",
            )
        ticket.status = "checked_in"
        ticket.checked_in_at = time_now()
        db.commit()
        db.refresh(ticket)
        return ticket

    def undo_check_in(self, db: Session, ticket: Ticket) -> Ticket:
        if ticket.status != "checked_in":
            raise HTTPException(
                status_code=400,
                detail="Ticket is not checked in",
            )
        ticket.status = "valid"
        ticket.checked_in_at = None
        db.commit()
        db.refresh(ticket)
        return ticket


ticket_service = TicketService()
