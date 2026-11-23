from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update

from core import *
from features.audit_log.service import audit_log_service
from features.notifications.service import notification_service
from features.ticket_types.models import TicketType
from features.ticket_types.service import ticket_type_service
from features.tickets.models import Ticket
from features.tickets.service import ticket_service

from .models import *
from .schemas import *


class OrderService:
    def create_order(self, db: Session, data: OrderCreate, user_id: UUID) -> Order:
        # Free stock held by abandoned checkouts before checking availability.
        self.expire_stale_orders(db)
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

    def hold_expires_at(self, order: Order) -> datetime:
        return order.created_at + timedelta(minutes=settings.ORDER_HOLD_MINUTES)

    def is_hold_expired(self, order: Order) -> bool:
        return order.status == "pending" and time_now() >= self.hold_expires_at(order)

    def expire_order(self, db: Session, order: Order) -> bool:
        """Releases a pending order's reserved stock and marks it expired (SRS 4.6).

        The status flip is a conditional UPDATE so a payment confirming the same
        order concurrently can't have its reservation released underneath it.
        """
        changed_id = db.scalar(
            update(Order)
            .where(Order.id == order.id, Order.status == "pending")
            .values(status="expired")
            .returning(Order.id)
            .execution_options(synchronize_session=False)
        )
        if changed_id is None:
            return False
        for item in order.items:
            ticket_type_service.release(db, item.ticket_type_id, item.quantity)
        audit_log_service.record(
            db,
            action="order_expired",
            entity_type="order",
            entity_id=order.id,
            event_id=order.event_id,
            actor_id=None,
            description=f"Checkout hold expired after {settings.ORDER_HOLD_MINUTES} min; "
            "reserved tickets released",
        )
        return True

    def expire_stale_orders(self, db: Session) -> int:
        """Expires every pending order whose hold has run out. Commits; returns the count."""
        cutoff = time_now() - timedelta(minutes=settings.ORDER_HOLD_MINUTES)
        stale = db.scalars(
            select(Order).where(Order.status == "pending", Order.created_at <= cutoff)
        ).all()
        expired = sum(1 for order in stale if self.expire_order(db, order))
        if expired:
            db.commit()
        return expired

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

    def refund_order(self, db: Session, order: Order, actor_id: UUID) -> Order:
        # Imported here to avoid a cycle: events and payments both import this module.
        from features.events.models import Event
        from features.payments.models import Payment
        from features.tickets.models import Ticket

        changed_id = db.scalar(
            update(Order)
            .where(Order.id == order.id, Order.status == "paid")
            .values(status="refunded")
            .returning(Order.id)
            .execution_options(synchronize_session=False)
        )
        if changed_id is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot refund an order with status '{order.status}'",
            )

        for item in order.items:
            db.execute(
                update(TicketType)
                .where(
                    TicketType.id == item.ticket_type_id,
                    TicketType.sold_count >= item.quantity,
                )
                .values(sold_count=TicketType.sold_count - item.quantity)
                .execution_options(synchronize_session=False)
            )

        db.execute(
            update(Ticket)
            .where(Ticket.order_id == order.id, Ticket.status != "refunded")
            .values(status="refunded")
            .execution_options(synchronize_session=False)
        )
        db.execute(
            update(Payment)
            .where(Payment.order_id == order.id, Payment.status == "succeeded")
            .values(status="refunded")
            .execution_options(synchronize_session=False)
        )

        audit_log_service.record(
            db,
            action="order_refunded",
            entity_type="order",
            entity_id=order.id,
            event_id=order.event_id,
            actor_id=actor_id,
            description=f"Refunded order {order.id} for {order.total_amount_kzt} tiyn",
        )
        db.commit()
        db.refresh(order)

        event = db.get(Event, order.event_id)
        notification_service.order_refunded(order, event.title if event else "BiletFlow event")
        return order


order_service = OrderService()
