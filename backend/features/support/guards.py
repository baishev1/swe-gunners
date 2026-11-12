from fastapi import Depends, HTTPException
from sqlalchemy import select

from core import *
from features.checkin.models import StaffAssignment
from features.events.models import Event
from features.users.models import User

from .dependencies import active_support_user
from .models import *
from .schemas import *


def valid_support_create(
    data: SupportCaseCreate,
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCaseCreate:
    if data.target == "platform" and user.role not in {"organizer", "platform_admin"}:
        raise HTTPException(status_code=403, detail="Platform support is for organizers")
    if data.event_id is not None:
        event = db.get(Event, data.event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        owns_event = event.organizer_id == user.id
        if data.target == "platform" and not owns_event and user.role != "platform_admin":
            raise HTTPException(status_code=403, detail="Event access denied")
        # Private-event access will use order/ticket ownership once those models land.
        if (
            data.target == "organizer"
            and not owns_event
            and user.role != "platform_admin"
            and (event.visibility != "public" or event.status != "published")
        ):
            raise HTTPException(status_code=404, detail="Event not found")
    return data


def support_case_staff(db: Session, case: SupportCase, user: User) -> bool:
    if user.role == "platform_admin":
        return True
    if case.target == "organizer" and case.event_id is not None:
        event = db.get(Event, case.event_id)
        if event is not None and event.organizer_id == user.id:
            return True
        return (
            db.scalar(
                select(StaffAssignment.id).where(
                    StaffAssignment.event_id == case.event_id,
                    StaffAssignment.user_id == user.id,
                    StaffAssignment.can_manage_support.is_(True),
                )
            )
            is not None
        )
    return False


def accessible_support_case(
    case_id: UUID,
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCase:
    case = db.get(SupportCase, case_id)
    if case is None or (case.requester_id != user.id and not support_case_staff(db, case, user)):
        raise HTTPException(status_code=404, detail="Support case not found")
    return case


def managed_support_case(
    case: SupportCase = Depends(accessible_support_case),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
) -> SupportCase:
    if not support_case_staff(db, case, user):
        raise HTTPException(status_code=403, detail="Only support staff can manage this case")
    return case
