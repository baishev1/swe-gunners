from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from core import *
from features.events.models import Event
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
        stmt = select(Event).where(Event.status != "cancelled")
        if user.role != "platform_admin":
            assigned = select(StaffAssignment.event_id).where(StaffAssignment.user_id == user.id)
            stmt = stmt.where(or_(Event.organizer_id == user.id, Event.id.in_(assigned)))
        return list(
            db.scalars(stmt.order_by(Event.start_time, Event.id).limit(limit).offset(offset))
        )


checkin_service = CheckInService()
