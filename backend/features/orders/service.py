from sqlalchemy import select

from core import *
from features.tickets.service import ticket_service

from .models import *
from .schemas import *


class OrderService:
    def create_order(self, db: Session, data: OrderCreate) -> Order:
        total_kzt = sum(item.unit_price_kzt * item.quantity for item in data.items)
        order = Order(
            user_id=data.user_id,
            event_id=data.event_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            total_amount_kzt=total_kzt,
            status="paid" if total_kzt == 0 else "pending",
        )
        db.add(order)
        db.flush()

        for item_data in data.items:
            item = OrderItem(
                order_id=order.id,
                ticket_type_id=item_data.ticket_type_id,
                ticket_type_name=item_data.ticket_type_name,
                unit_price_kzt=item_data.unit_price_kzt,
                quantity=item_data.quantity,
            )
            db.add(item)

        db.commit()
        db.refresh(order)

        if total_kzt == 0:
            ticket_service.issue_tickets_for_order(db=db, order=order)

        return order

    def list_orders(
        self,
        db: Session,
        user_id: UUID | None = None,
        event_id: UUID | None = None,
        status: str | None = None,
    ) -> list[Order]:
        stmt = select(Order)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)
        if event_id:
            stmt = stmt.where(Order.event_id == event_id)
        if status:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.order_by(Order.created_at.desc())
        return list(db.scalars(stmt).all())

    def cancel_order(self, db: Session, order: Order) -> Order:
        order.status = "cancelled"
        db.commit()
        db.refresh(order)
        return order


order_service = OrderService()
