from contextlib import suppress

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError

from core import *
from features.events.models import Event
from features.orders.models import Order
from features.tickets.models import Ticket
from features.users.models import User

from .models import *
from .schemas import *


class CheckInService:
    def assign_staff(
        self, db: Session, event: Event, data: StaffAssignmentCreate
    ) -> StaffAssignment:
        assignment = StaffAssignment(**data.model_dump(), event_id=event.id)
        db.add(assignment)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(
                select(StaffAssignment).where(
                    StaffAssignment.event_id == event.id,
                    StaffAssignment.user_id == data.user_id,
                )
            )
            if existing is not None:
                raise HTTPException(status_code=409, detail="User is already assigned") from None
            raise
        db.refresh(assignment)
        return assignment

    def list_staff(
        self, db: Session, event: Event, limit: int, offset: int
    ) -> list[StaffAssignment]:
        stmt = (
            select(StaffAssignment)
            .where(StaffAssignment.event_id == event.id)
            .order_by(StaffAssignment.id)
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all())

    def revoke_staff(self, db: Session, assignment: StaffAssignment) -> None:
        db.delete(assignment)
        db.commit()

    def list_events(self, db: Session, user: User, limit: int, offset: int) -> list[Event]:
        stmt = select(Event).where(Event.status.not_in(["cancelled", "suspended"]))
        if user.role != "platform_admin":
            assigned = select(StaffAssignment.event_id).where(StaffAssignment.user_id == user.id)
            stmt = stmt.where(or_(Event.organizer_id == user.id, Event.id.in_(assigned)))
        return list(
            db.scalars(stmt.order_by(Event.start_time, Event.id).limit(limit).offset(offset))
        )

    def undoable_event_ids(self, db: Session, user: User, events: list[Event]) -> set[UUID]:
        if user.role == "platform_admin":
            return {event.id for event in events}
        owned = {event.id for event in events if event.organizer_id == user.id}
        granted = db.scalars(
            select(StaffAssignment.event_id).where(
                StaffAssignment.user_id == user.id,
                StaffAssignment.can_undo_check_in.is_(True),
            )
        )
        return owned | set(granted)

    def search_attendees(
        self, db: Session, event: Event, q: str | None, limit: int, offset: int
    ) -> list[tuple[Ticket, str]]:
        stmt = (
            select(Ticket, Order.status)
            .join(Order, Order.id == Ticket.order_id)
            .where(Ticket.event_id == event.id)
        )
        if q:
            pattern = f"%{q}%"
            matches: list[ColumnElement[bool]] = [
                Ticket.attendee_name.ilike(pattern),
                Ticket.attendee_email.ilike(pattern),
            ]
            with suppress(ValueError):
                matches.append(Ticket.id == UUID(q))
            stmt = stmt.where(or_(*matches))
        stmt = stmt.order_by(Ticket.attendee_name, Ticket.id).limit(limit).offset(offset)
        return [(ticket, order_status) for ticket, order_status in db.execute(stmt)]

    def summary(self, db: Session, event: Event) -> tuple[int, int]:
        registered, checked_in = db.execute(
            select(
                func.count().filter(Ticket.status.in_(["valid", "checked_in"])),
                func.count().filter(Ticket.status == "checked_in"),
            )
            .join(Order, Order.id == Ticket.order_id)
            .where(Ticket.event_id == event.id, Order.status == "paid")
        ).one()
        return registered, checked_in


checkin_service = CheckInService()
