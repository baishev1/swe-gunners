from fastapi import Depends, HTTPException
from sqlalchemy import func, select

from core import *
from features.events.models import Event
from features.users.dependencies import active_user
from features.users.models import User

from .models import *
from .schemas import *


def managed_event(
    event_id: UUID,
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
) -> Event:
    event = db.get(Event, event_id)
    if event is None or (event.organizer_id != user.id and user.role != "platform_admin"):
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def valid_staff_assignment(
    data: StaffAssignmentCreate,
    event: Event = Depends(managed_event),
    db: Session = Depends(get_db),
) -> StaffAssignmentCreate:
    if data.email:
        email = data.email.strip().lower()
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="No BiletFlow account uses this email. Ask the person to register first.",
            )
        data = data.model_copy(update={"user_id": user.id, "email": None})
    else:
        user = db.get(User, data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Cannot assign an inactive user")
    if user.id == event.organizer_id:
        raise HTTPException(status_code=400, detail="The event owner already has access")
    return data


def managed_assignment(
    assignment_id: UUID,
    event: Event = Depends(managed_event),
    db: Session = Depends(get_db),
) -> StaffAssignment:
    assignment = db.get(StaffAssignment, assignment_id)
    if assignment is None or assignment.event_id != event.id:
        raise HTTPException(status_code=404, detail="Staff assignment not found")
    return assignment


def assigned_event(
    event_id: UUID,
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
) -> Event:
    """Use on ticket verification/check-in with the selected event_id."""
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    assignment = db.scalar(
        select(StaffAssignment).where(
            StaffAssignment.event_id == event.id,
            StaffAssignment.user_id == user.id,
        )
    )
    if event.organizer_id != user.id and user.role != "platform_admin" and assignment is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status in {"cancelled", "suspended"}:
        raise HTTPException(status_code=400, detail=f"Cannot check in to a {event.status} event")
    return event


def undo_check_in_event(
    event: Event = Depends(assigned_event),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
) -> Event:
    """Use on undo-check-in; ordinary scanner access is insufficient."""
    if event.organizer_id == user.id or user.role == "platform_admin":
        return event
    assignment = db.scalar(
        select(StaffAssignment).where(
            StaffAssignment.event_id == event.id,
            StaffAssignment.user_id == user.id,
            StaffAssignment.can_undo_check_in.is_(True),
        )
    )
    if assignment is None:
        raise HTTPException(status_code=403, detail="Check-in reversal is not permitted")
    return event
