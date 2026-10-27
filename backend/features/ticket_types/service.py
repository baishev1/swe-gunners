from sqlalchemy import func, select

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


ticket_type_service = TicketTypeService()
