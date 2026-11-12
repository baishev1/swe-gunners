import secrets
from io import BytesIO

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select, update

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event
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
        user_id: UUID,
        order_id: UUID | None = None,
        event_id: UUID | None = None,
    ) -> list[Ticket]:
        stmt = (
            select(Ticket).join(Order, Order.id == Ticket.order_id).where(Order.user_id == user_id)
        )
        if order_id:
            stmt = stmt.where(Ticket.order_id == order_id)
        if event_id:
            stmt = stmt.where(Ticket.event_id == event_id)
        stmt = stmt.order_by(Ticket.created_at.asc())
        return list(db.scalars(stmt).all())

    def list_event_attendees(self, db: Session, event_id: UUID) -> list[tuple[Ticket, str]]:
        stmt = (
            select(Ticket, Order.status)
            .join(Order, Order.id == Ticket.order_id)
            .where(Ticket.event_id == event_id)
            .order_by(Ticket.created_at.desc())
        )
        return [(ticket, order_status) for ticket, order_status in db.execute(stmt)]

    def get_ticket_by_qr_token(self, db: Session, qr_token: str) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.qr_token == qr_token)
        return db.scalar(stmt)

    def check_in_ticket(self, db: Session, ticket: Ticket, actor_id: UUID) -> Ticket:
        return self._transition(db, ticket, actor_id, reverse=False)

    def undo_check_in(self, db: Session, ticket: Ticket, actor_id: UUID) -> Ticket:
        return self._transition(db, ticket, actor_id, reverse=True)

    def _transition(self, db: Session, ticket: Ticket, actor_id: UUID, reverse: bool) -> Ticket:
        expected = "checked_in" if reverse else "valid"
        target = "valid" if reverse else "checked_in"
        paid_order = (
            select(Order.id)
            .where(
                Order.id == Ticket.order_id,
                Order.event_id == Ticket.event_id,
                Order.status == "paid",
            )
            .exists()
        )
        active_event = (
            select(Event.id)
            .where(
                Event.id == Ticket.event_id,
                Event.status.not_in(["cancelled", "suspended"]),
            )
            .exists()
        )
        # The database checks the current state, even if another scanner changed it
        # after this request loaded the ticket. The timestamp also protects stale undo requests.
        stmt = (
            update(Ticket)
            .where(
                Ticket.id == ticket.id,
                Ticket.event_id == ticket.event_id,
                Ticket.status == expected,
                Ticket.checked_in_at == ticket.checked_in_at,
                paid_order,
                active_event,
            )
            .values(status=target, checked_in_at=None if reverse else time_now())
            .returning(Ticket.id)
            .execution_options(synchronize_session=False)
        )
        changed_id = db.scalar(stmt)
        if changed_id is None:
            db.rollback()
            detail = (
                "Ticket is not checked in or is not eligible for admission"
                if reverse
                else "Ticket is already checked in or is not eligible for admission"
            )
            raise HTTPException(status_code=400, detail=detail)
        audit_log_service.record(
            db,
            action="ticket_check_in_reversed" if reverse else "ticket_checked_in",
            entity_type="ticket",
            entity_id=ticket.id,
            event_id=ticket.event_id,
            actor_id=actor_id,
            description="Reversed ticket check-in" if reverse else "Checked in ticket",
        )
        db.commit()
        db.refresh(ticket)
        return ticket

    def generate_pdf_ticket(self, db: Session, ticket: Ticket) -> bytes:
        event = db.get(Event, ticket.event_id)
        event_title = event.title if event else "BiletFlow Event"
        event_venue = f"{event.venue.name}, {event.venue.address}" if event else "Venue: TBA"
        event_time = (
            event.start_time.strftime("%d %B %Y, %H:%M")
            if event
            else ticket.created_at.strftime("%d %B %Y")
        )

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TicketTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b"),
        )
        subtitle_style = ParagraphStyle(
            "TicketSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
        )
        label_style = ParagraphStyle(
            "TicketLabel",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        )
        val_style = ParagraphStyle(
            "TicketVal",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )

        qr_code = QrCodeWidget(ticket.qr_token)
        bounds = qr_code.getBounds()
        qr_w = bounds[2] - bounds[0]
        qr_h = bounds[3] - bounds[1]
        drawing = Drawing(150, 150, transform=[150.0 / qr_w, 0, 0, 150.0 / qr_h, 0, 0])
        drawing.add(qr_code)

        left_content = [
            Paragraph("BILETFLOW ADMISSION TICKET", label_style),
            Spacer(1, 4),
            Paragraph(event_title, title_style),
            Spacer(1, 10),
            Paragraph("DATE & TIME", label_style),
            Paragraph(event_time, val_style),
            Spacer(1, 8),
            Paragraph("VENUE", label_style),
            Paragraph(event_venue, val_style),
            Spacer(1, 8),
            Paragraph("TICKET TYPE", label_style),
            Paragraph(ticket.ticket_type_name, val_style),
            Spacer(1, 8),
            Paragraph("ATTENDEE", label_style),
            Paragraph(f"{ticket.attendee_name} ({ticket.attendee_email})", val_style),
            Spacer(1, 8),
            Paragraph("TICKET ID", label_style),
            Paragraph(str(ticket.id), subtitle_style),
        ]

        right_content = [
            drawing,
            Spacer(1, 8),
            Paragraph("Scan at entrance", subtitle_style),
            Paragraph(f"Status: {ticket.status.upper()}", val_style),
        ]

        card_table = Table([[left_content, right_content]], colWidths=[330, 185])
        card_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 16),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                    ("LEFTPADDING", (0, 0), (-1, -1), 16),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ]
            )
        )

        elements = [
            card_table,
            Spacer(1, 16),
            Paragraph(
                "Please present this ticket on your device or print on standard A4 paper. "
                "Each QR code allows one entry and will be invalidated once scanned.",
                subtitle_style,
            ),
        ]

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


ticket_service = TicketService()
