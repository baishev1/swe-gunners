from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.orders.models import Order
from features.tickets.models import Ticket


class SupportCase(DbBase):
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("event.id"), index=True)
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), default=None)
    target: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30))
    subject: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="open")
    # Context the case was opened from (SRS 4.13); filled from the ticket or order.
    order_id: Mapped[UUID | None] = mapped_column(ForeignKey("order.id"), default=None)
    ticket_id: Mapped[UUID | None] = mapped_column(ForeignKey("ticket.id"), default=None)

    order: Mapped[Order | None] = relationship(lazy="joined")
    ticket: Mapped[Ticket | None] = relationship(lazy="joined")

    @property
    def order_status(self) -> str | None:
        return self.order.status if self.order else None

    @property
    def order_total_kzt(self) -> int | None:
        return self.order.total_amount_kzt if self.order else None

    @property
    def ticket_type_name(self) -> str | None:
        return self.ticket.ticket_type_name if self.ticket else None

    @property
    def ticket_status(self) -> str | None:
        return self.ticket.status if self.ticket else None


class SupportMessage(DbBase):
    case_id: Mapped[UUID] = mapped_column(ForeignKey("support_case.id"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    body: Mapped[str] = mapped_column(Text)
