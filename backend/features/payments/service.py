from uuid import uuid4

from sqlalchemy import select

from core import *
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
            db.commit()
            db.refresh(payment)
            return payment

        payment = Payment(
            order_id=order.id,
            amount_kzt=order.total_amount_kzt,
            status="succeeded",
            provider="simulation",
            transaction_id=tx_id,
        )
        db.add(payment)
        order_service.confirm_sale(db, order)
        db.commit()
        db.refresh(payment)

        ticket_service.issue_tickets_for_order(db=db, order=order)
        return payment

    def get_payment_by_order(self, db: Session, order_id: UUID) -> Payment | None:
        stmt = (
            select(Payment).where(Payment.order_id == order_id).order_by(Payment.created_at.desc())
        )
        return db.scalar(stmt)


payment_service = PaymentService()
