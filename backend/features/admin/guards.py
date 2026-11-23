from fastapi import Depends, HTTPException, status

from core import *
from features.auth.guards import get_current_user
from features.events.guards import valid_event_id
from features.events.models import Event
from features.users.models import User


def valid_user_id(user_id: UUID, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def suspendable_user_guard(
    target: User = Depends(valid_user_id),
    admin: User = Depends(get_current_user),
) -> User:
    if target.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot suspend your own account",
        )
    if not target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already suspended",
        )
    return target


def reinstatable_user_guard(target: User = Depends(valid_user_id)) -> User:
    if target.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not suspended",
        )
    return target


def reinstatable_event_guard(event: Event = Depends(valid_event_id)) -> Event:
    if event.status != "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not suspended",
        )
    return event


def suspendable_event_guard(event: Event = Depends(valid_event_id)) -> Event:
    if event.status in ("suspended", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event is already {event.status}",
        )
    return event
