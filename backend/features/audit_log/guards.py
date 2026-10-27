from fastapi import Depends, HTTPException, status

from core import *
from features.auth.guards import get_current_user
from features.events.guards import valid_event_id
from features.events.models import Event
from features.users.models import User


def event_history_guard(
    event: Event = Depends(valid_event_id),
    user: User = Depends(get_current_user),
) -> Event:
    is_owner = user.role == "organizer" and event.organizer_id == user.id
    if not is_owner and user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event
