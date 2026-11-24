from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from core import *
from features.auth.service import auth_service

if TYPE_CHECKING:
    from features.orders.models import Order
    from features.tickets.models import Ticket


logger = logging.getLogger(__name__)


class NotificationService:
    """Transactional emails for the order lifecycle (SRS 4.10).

    Delivery goes through the auth feature's SMTP helper so local runs and tests
    keep using the same log-only fallback as account emails.
    """

    def order_confirmation(self, order: Order, tickets: list[Ticket], event_title: str) -> None:
        def describe(ticket: Ticket) -> str:
            seat = (
                f", section {ticket.section} row {ticket.row} seat {ticket.seat}"
                if ticket.section
                else ""
            )
            return f"- {ticket.ticket_type_name}{seat}: {ticket.id}"

        lines = "\n".join(describe(ticket) for ticket in tickets)
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
                "Paid tickets have been refunded in full and free registrations are cancelled.",
            )

    def event_updated(self, event_title: str, changes: list[str], emails: list[str]) -> None:
        summary = "\n".join(f"- {change}" for change in changes)
        for email in emails:
            self._send(
                email,
                f"Event update: {event_title}",
                f"The organizer changed details of {event_title}:\n{summary}\n\n"
                "Your tickets stay valid. If you added the event to your calendar, "
                "please update it.",
            )

    def payout_status_changed(
        self, email: str, event_title: str, status: str, reason: str | None = None
    ) -> None:
        """Organizer payout status (SRS 4.10). Payouts are simulated in the MVP."""
        messages = {
            "active": "Paid ticket sales are now active. Ticket revenue will be paid out to "
            "your registered payout account (demonstration only, no real money moves).",
            "suspended": "Paid ticket sales and payouts are suspended by a platform administrator.",
            "reinstated": "Paid ticket sales and payouts were reinstated.",
        }
        body = messages[status]
        if reason:
            body += f"\nReason: {reason}"
        self._send(email, f"Payout status for {event_title}: {status}", body)

    def support_reply(self, email: str, case_subject: str, case_id: UUID, body: str) -> None:
        preview = body if len(body) <= 300 else body[:297] + "..."
        self._send(
            email,
            f"New reply in support case: {case_subject}",
            f"{preview}\n\nOpen the conversation: {self._case_url(case_id)}",
        )

    def support_assigned(
        self, email: str, case_subject: str, case_id: UUID, assignee_name: str
    ) -> None:
        self._send(
            email,
            f"Support case assigned: {case_subject}",
            f"{assignee_name} is now handling your support case.\n\n"
            f"Open the conversation: {self._case_url(case_id)}",
        )

    def support_status_changed(
        self, email: str, case_subject: str, case_id: UUID, status: str
    ) -> None:
        label = status.replace("_", " ").capitalize()
        self._send(
            email,
            f"Support case status: {label}",
            f'Your support case "{case_subject}" is now: {label}.\n\n'
            f"Open the conversation: {self._case_url(case_id)}",
        )

    def _case_url(self, case_id: UUID) -> str:
        return f"{settings.FRONTEND_URL}/support/case?case_id={case_id}"

    def event_report_created(
        self, email: str, event_title: str, category: str, report_id: UUID
    ) -> None:
        self._send(
            email,
            f"New event report: {event_title}",
            f"An attendee reported {event_title} ({category.replace('_', ' ')}).\n"
            f"Report ID: {report_id}\n\n"
            f"Review it in the admin panel: {settings.FRONTEND_URL}/admin",
        )

    def _send(self, to: str, subject: str, body: str) -> None:
        """Sends after the business change is committed, so a mail failure must not fail
        the request: the order, refund or support message already happened."""
        try:
            auth_service.send_email(to, subject, body)
        except Exception:
            logger.exception("Could not send email %r to %s", subject, to)

    def _money(self, amount: int) -> str:
        return f"{amount / 100:.2f} KZT"


notification_service = NotificationService()
