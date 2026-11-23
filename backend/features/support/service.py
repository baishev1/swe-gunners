from sqlalchemy import or_, select

from core import *
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.notifications.service import notification_service
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
        self._notify_reply(db, case, user, data.message)
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
        self._notify_reply(db, case, user, message.body)
        return message

    def update_status(
        self, db: Session, case: SupportCase, data: SupportStatusUpdate
    ) -> SupportCase:
        changed = case.status != data.status
        case.status = data.status
        db.commit()
        db.refresh(case)
        requester = db.get(User, case.requester_id)
        if changed and requester is not None:
            notification_service.support_status_changed(
                requester.email, case.subject, case.id, case.status
            )
        return case

    def assign_to_self(self, db: Session, case: SupportCase, user: User) -> SupportCase:
        changed = case.assignee_id != user.id
        case.assignee_id = user.id
        db.commit()
        db.refresh(case)
        requester = db.get(User, case.requester_id)
        if changed and requester is not None and requester.id != user.id:
            notification_service.support_assigned(
                requester.email, case.subject, case.id, user.full_name
            )
        return case

    def _notify_reply(self, db: Session, case: SupportCase, author: User, body: str) -> None:
        """Emails the other side of the conversation about a new message (SRS 4.10, 4.13)."""
        for email in self._reply_recipients(db, case, author):
            notification_service.support_reply(email, case.subject, case.id, body)

    def _reply_recipients(self, db: Session, case: SupportCase, author: User) -> list[str]:
        if author.id != case.requester_id:
            requester = db.get(User, case.requester_id)
            return [requester.email] if requester is not None else []
        # Requester wrote: tell whoever handles the case, or the default owner if nobody does.
        if case.assignee_id is not None:
            assignee = db.get(User, case.assignee_id)
            return [assignee.email] if assignee is not None else []
        if case.target == "organizer" and case.event_id is not None:
            event = db.get(Event, case.event_id)
            organizer = db.get(User, event.organizer_id) if event is not None else None
            if organizer is not None and organizer.id != author.id:
                return [organizer.email]
            return []
        if case.target == "platform":
            return list(
                db.scalars(
                    select(User.email).where(User.role == "platform_admin", User.id != author.id)
                )
            )
        return []


support_service = SupportService()
