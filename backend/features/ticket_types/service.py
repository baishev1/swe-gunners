from typing import Any, cast

from sqlalchemy import CursorResult, Update, func, select, update

from core import *
from features.audit_log.service import audit_log_service

from .models import *
from .schemas import *


class TicketTypeService:
    def create_ticket_type(
        self, db: Session, event: Event, data: TicketTypeCreate, actor_id: UUID | None = None
    ) -> TicketType:
        ticket_type = TicketType(**data.model_dump(), event_id=event.id)
        db.add(ticket_type)
        db.flush()
        self._record(
            db,
            ticket_type,
            "ticket_type_created",
            f"Added ticket type {ticket_type.name}: {ticket_type.quantity} at "
            f"{ticket_type.price} tiyn",
            actor_id,
        )
        db.commit()
        db.refresh(ticket_type)
        return ticket_type

    def update_ticket_type(
        self,
        db: Session,
        ticket_type: TicketType,
        data: TicketTypeUpdate,
        actor_id: UUID | None = None,
    ) -> TicketType:
        update_data = data.model_dump(exclude_unset=True)
        old_price, old_quantity = ticket_type.price, ticket_type.quantity
        for key, value in update_data.items():
            setattr(ticket_type, key, value)
        if ticket_type.price != old_price:
            self._record(
                db,
                ticket_type,
                "ticket_price_changed",
                f"Changed {ticket_type.name} price from {old_price} to {ticket_type.price} tiyn",
                actor_id,
            )
        if ticket_type.quantity != old_quantity:
            self._record(
                db,
                ticket_type,
                "ticket_capacity_changed",
                f"Changed {ticket_type.name} quantity from {old_quantity} to "
                f"{ticket_type.quantity}",
                actor_id,
            )
        db.commit()
        db.refresh(ticket_type)
        return ticket_type

    def list_ticket_types(
        self, db: Session, event_id: UUID, include_hidden: bool = False
    ) -> list[TicketType]:
        stmt = select(TicketType).where(TicketType.event_id == event_id)
        if not include_hidden:
            stmt = stmt.where(TicketType.is_hidden.is_(False))
        stmt = stmt.order_by(TicketType.created_at.asc())
        return list(db.scalars(stmt).all())

    def total_quantity(self, db: Session, event_id: UUID, exclude_id: UUID | None = None) -> int:
        stmt = select(func.coalesce(func.sum(TicketType.quantity), 0)).where(
            TicketType.event_id == event_id
        )
        if exclude_id:
            stmt = stmt.where(TicketType.id != exclude_id)
        return db.scalar(stmt) or 0

    # Stock changes run as a single conditional UPDATE so concurrent checkouts can't oversell.
    # The caller commits, so an order can touch several ticket types in one transaction.
    def reserve(self, db: Session, ticket_type_id: UUID, quantity: int) -> bool:
        stmt = (
            update(TicketType)
            .where(
                TicketType.id == ticket_type_id,
                TicketType.quantity - TicketType.reserved_count - TicketType.sold_count >= quantity,
            )
            .values(reserved_count=TicketType.reserved_count + quantity)
        )
        return self._update_one(db, stmt)

    def release(self, db: Session, ticket_type_id: UUID, quantity: int) -> bool:
        stmt = (
            update(TicketType)
            .where(TicketType.id == ticket_type_id, TicketType.reserved_count >= quantity)
            .values(reserved_count=TicketType.reserved_count - quantity)
        )
        return self._update_one(db, stmt)

    def confirm_sale(self, db: Session, ticket_type_id: UUID, quantity: int) -> bool:
        stmt = (
            update(TicketType)
            .where(TicketType.id == ticket_type_id, TicketType.reserved_count >= quantity)
            .values(
                reserved_count=TicketType.reserved_count - quantity,
                sold_count=TicketType.sold_count + quantity,
            )
        )
        return self._update_one(db, stmt)

    def release_sale(self, db: Session, ticket_type_id: UUID, quantity: int) -> bool:
        stmt = (
            update(TicketType)
            .where(TicketType.id == ticket_type_id, TicketType.sold_count >= quantity)
            .values(sold_count=TicketType.sold_count - quantity)
        )
        return self._update_one(db, stmt)

    # refunded_count folds cancelled registrations in: both return the seat to inventory.
    def attach_ticket_stats(self, db: Session, ticket_types: list[TicketType]) -> list[TicketType]:
        # Imported lazily: features.tickets pulls in orders, which imports this module.
        from features.tickets.models import Ticket

        if not ticket_types:
            return ticket_types
        rows = db.execute(
            select(Ticket.ticket_type_id, Ticket.status, func.count())
            .where(Ticket.ticket_type_id.in_([t.id for t in ticket_types]))
            .group_by(Ticket.ticket_type_id, Ticket.status)
        ).all()
        stats: dict[UUID, dict[str, int]] = {}
        for ticket_type_id, ticket_status, count in rows:
            stats.setdefault(ticket_type_id, {})[ticket_status] = count
        for ticket_type in ticket_types:
            counts = stats.get(ticket_type.id, {})
            refunded = counts.get("refunded", 0) + counts.get("cancelled", 0)
            setattr(ticket_type, "refunded_count", refunded)  # noqa: B010
            setattr(ticket_type, "checked_in_count", counts.get("checked_in", 0))  # noqa: B010
        return ticket_types

    def _record(
        self,
        db: Session,
        ticket_type: TicketType,
        action: str,
        description: str,
        actor_id: UUID | None,
    ) -> None:
        audit_log_service.record(
            db,
            action=action,
            entity_type="ticket_type",
            entity_id=ticket_type.id,
            description=description,
            event_id=ticket_type.event_id,
            actor_id=actor_id,
        )

    def _update_one(self, db: Session, stmt: Update) -> bool:
        result = cast(CursorResult[Any], db.execute(stmt))
        return result.rowcount == 1


ticket_type_service = TicketTypeService()
