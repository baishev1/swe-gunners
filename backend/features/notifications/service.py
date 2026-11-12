from __future__ import annotations

from typing import TYPE_CHECKING

from core import *
from features.auth.service import auth_service

if TYPE_CHECKING:
    from features.orders.models import Order
    from features.tickets.models import Ticket


class NotificationService:
    """Transactional emails for the order lifecycle (SRS 4.10).

    Delivery goes through the auth feature's SMTP helper so local runs and tests
    keep using the same log-only fallback as account emails.
    """

    def order_confirmation(self, order: Order, tickets: list[Ticket], event_title: str) -> None:
        lines = "\n".join(f"- {ticket.ticket_type_name}: {ticket.id}" for ticket in tickets)
        self._send(
            order.customer_email,
            f"Your tickets for {event_title}",
            f"Your order for {event_title} is confirmed.\n"
            f"{len(tickets)} ticket(s), total {self._money(order.total_amount_kzt)}.\n\n"
            f"{lines}\n\n"
            f"Open your tickets: {settings.FRONTEND_URL}/tickets?order_id={order.id}",
        )

    def payment_failed(self, order: Order, event_title: str) -> None:
        self._send(
            order.customer_email,
            f"Payment failed for {event_title}",
            f"We could not process your payment of {self._money(order.total_amount_kzt)} "
            f"for {event_title}.\n"
            f"Your tickets have not been issued. Try again from {settings.FRONTEND_URL}/orders",
        )

    def order_refunded(self, order: Order, event_title: str) -> None:
        self._send(
            order.customer_email,
            f"Refund issued for {event_title}",
            f"Your order for {event_title} was refunded in full "
            f"({self._money(order.total_amount_kzt)}).\n"
            "The tickets from this order are no longer valid for entry.",
        )

    def event_cancelled(self, event_title: str, emails: list[str]) -> None:
        for email in emails:
            self._send(
                email,
                f"Event cancelled: {event_title}",
                f"{event_title} has been cancelled.\n"
                "The organizer will contact you about a refund if you paid for a ticket.",
            )

    def _send(self, to: str, subject: str, body: str) -> None:
        auth_service.send_email(to, subject, body)

    def _money(self, amount: int) -> str:
        return f"{amount / 100:.2f} KZT"


notification_service = NotificationService()
