from uuid import uuid4

from sqlalchemy import select

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event
from features.notifications.service import notification_service
from features.orders.models import Order
from features.orders.service import order_service
from features.tickets.service import ticket_service

from .models import *
from .schemas import *


class PaymentService:
    def process_simulation(
        self,
        db: Session,
        order: Order,
        simulate_failure: bool = False,
    ) -> Payment:
        tx_id = f"sim_{uuid4().hex[:16]}"

        if simulate_failure:
            payment = Payment(
                order_id=order.id,
                amount_kzt=order.total_amount_kzt,
                status="failed",
                provider="simulation",
                transaction_id=tx_id,
            )
            db.add(payment)
            db.flush()
            self._record(db, payment, order, "payment_failed", "failed")
            db.commit()
            db.refresh(payment)
            event = db.get(Event, order.event_id)
            notification_service.payment_failed(order, event.title if event else "BiletFlow event")
            return payment

        payment = Payment(
            order_id=order.id,
            amount_kzt=order.total_amount_kzt,
            status="succeeded",
            provider="simulation",
            transaction_id=tx_id,
        )
        db.add(payment)
        db.flush()
        order_service.confirm_sale(db, order)
        self._record(db, payment, order, "payment_succeeded", "succeeded")
        db.commit()
        db.refresh(payment)

        ticket_service.issue_tickets_for_order(db=db, order=order)
        return payment

    def _record(
        self, db: Session, payment: Payment, order: Order, action: str, outcome: str
    ) -> None:
        """Every payment attempt goes to the audit log (SRS 4.9); amounts are in tiyn."""
        audit_log_service.record(
            db,
            action=action,
            entity_type="payment",
            entity_id=payment.id,
            description=f"Simulated payment {outcome}: {payment.amount_kzt} tiyn for order "
            f"{order.id} ({payment.transaction_id})",
            event_id=order.event_id,
            actor_id=order.user_id,
        )

    def get_payment_by_order(self, db: Session, order_id: UUID) -> Payment | None:
        stmt = (
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
        )
        return db.scalar(stmt)


payment_service = PaymentService()
