from fastapi import HTTPException, status
from sqlalchemy import select, update

from core import *
from features.audit_log.service import audit_log_service
from features.ticket_types.models import TicketType
from features.ticket_types.service import ticket_type_service
from features.tickets.models import Ticket
from features.tickets.service import ticket_service

from .models import *
from .schemas import *


class OrderService:
    def create_order(self, db: Session, data: OrderCreate, user_id: UUID) -> Order:
        order = Order(**data.model_dump(exclude={"items"}), user_id=user_id, total_amount_kzt=0)
        db.add(order)
        db.flush()

        for item_data in data.items:
            ticket_type = db.get(TicketType, item_data.ticket_type_id)
            assert ticket_type is not None
            if not ticket_type_service.reserve(db, ticket_type.id, item_data.quantity):
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Not enough {ticket_type.name} tickets left",
                )
            order.items.append(
                OrderItem(
                    ticket_type_id=ticket_type.id,
                    ticket_type_name=ticket_type.name,
                    unit_price_kzt=ticket_type.price,
                    quantity=item_data.quantity,
                )
            )
            order.total_amount_kzt += ticket_type.price * item_data.quantity

        if order.total_amount_kzt == 0:
            self.confirm_sale(db, order)
        db.commit()
        db.refresh(order)

        if order.status == "paid":
            ticket_service.issue_tickets_for_order(db=db, order=order)

        return order

    def confirm_sale(self, db: Session, order: Order) -> None:
        for item in order.items:
            ticket_type_service.confirm_sale(db, item.ticket_type_id, item.quantity)
        order.status = "paid"

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

    def cancel_order(self, db: Session, order: Order, actor_id: UUID) -> Order:
        if order.status == "pending":
            for item in order.items:
                ticket_type_service.release(db, item.ticket_type_id, item.quantity)
        elif order.status == "paid":
            cancelled_type_ids = (
                db.execute(
                    update(Ticket)
                    .where(Ticket.order_id == order.id, Ticket.status == "valid")
                    .values(status="cancelled")
                    .returning(Ticket.ticket_type_id)
                    .execution_options(synchronize_session=False)
                )
                .scalars()
                .all()
            )
            restocked: dict[UUID, int] = {}
            for ticket_type_id in cancelled_type_ids:
                restocked[ticket_type_id] = restocked.get(ticket_type_id, 0) + 1
            for ticket_type_id, quantity in restocked.items():
                ticket_type_service.release_sale(db, ticket_type_id, quantity)
        order.status = "cancelled"
        audit_log_service.record(
            db,
            action="order_cancelled",
            entity_type="order",
            entity_id=order.id,
            event_id=order.event_id,
            actor_id=actor_id,
            description="Cancelled order",
        )
        db.commit()
        db.refresh(order)
        return order


order_service = OrderService()
