from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.auth.guards import require_role
from features.users.models import User

from .models import *


def organizer_profile_guard(
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
) -> OrganizerProfile:
    profile = db.scalar(select(OrganizerProfile).where(OrganizerProfile.user_id == user.id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organizer profile not found",
        )
    return profile
