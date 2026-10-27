from typing import Any, cast

from sqlalchemy import CursorResult, Update, func, select, update

from core import *

from .models import *
from .schemas import *


class TicketTypeService:
    def create_ticket_type(self, db: Session, event: Event, data: TicketTypeCreate) -> TicketType:
        ticket_type = TicketType(**data.model_dump(), event_id=event.id)
        db.add(ticket_type)
        db.commit()
        db.refresh(ticket_type)
        return ticket_type

    def update_ticket_type(
        self, db: Session, ticket_type: TicketType, data: TicketTypeUpdate
    ) -> TicketType:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(ticket_type, key, value)
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

    def _update_one(self, db: Session, stmt: Update) -> bool:
        result = cast(CursorResult[Any], db.execute(stmt))
        return result.rowcount == 1


ticket_type_service = TicketTypeService()
