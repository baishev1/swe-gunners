from sqlalchemy import or_, select

from core import *
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.users.models import User

from .models import *
from .schemas import *


class SupportService:
    def create_case(self, db: Session, data: SupportCaseCreate, user: User) -> SupportCase:
        case = SupportCase(**data.model_dump(exclude={"message"}), requester_id=user.id)
        db.add(case)
        db.flush()
        db.add(SupportMessage(case_id=case.id, author_id=user.id, body=data.message))
        db.commit()
        db.refresh(case)
        return case

    def list_cases(self, db: Session, user: User, limit: int, offset: int) -> list[SupportCase]:
        stmt = select(SupportCase)
        if user.role != "platform_admin":
            owned_events = select(Event.id).where(Event.organizer_id == user.id)
            support_events = select(StaffAssignment.event_id).where(
                StaffAssignment.user_id == user.id,
                StaffAssignment.can_manage_support.is_(True),
            )
            stmt = stmt.where(
                or_(
                    SupportCase.requester_id == user.id,
                    (SupportCase.target == "organizer") & SupportCase.event_id.in_(owned_events),
                    (SupportCase.target == "organizer") & SupportCase.event_id.in_(support_events),
                )
            )
        stmt = stmt.order_by(SupportCase.updated_at.desc(), SupportCase.id.desc())
        return list(db.scalars(stmt.limit(limit).offset(offset)).all())

    def list_messages(
        self, db: Session, case: SupportCase, limit: int, offset: int
    ) -> list[SupportMessage]:
        stmt = (
            select(SupportMessage)
            .where(SupportMessage.case_id == case.id)
            .order_by(SupportMessage.created_at, SupportMessage.id)
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all())

    def add_message(
        self, db: Session, case: SupportCase, user: User, data: SupportMessageCreate
    ) -> SupportMessage:
        message = SupportMessage(**data.model_dump(), case_id=case.id, author_id=user.id)
        db.add(message)
        case.updated_at = time_now()
        db.commit()
        db.refresh(message)
        return message

    def update_status(
        self, db: Session, case: SupportCase, data: SupportStatusUpdate
    ) -> SupportCase:
        case.status = data.status
        db.commit()
        db.refresh(case)
        return case

    def assign_to_self(self, db: Session, case: SupportCase, user: User) -> SupportCase:
        case.assignee_id = user.id
        db.commit()
        db.refresh(case)
        return case


support_service = SupportService()
