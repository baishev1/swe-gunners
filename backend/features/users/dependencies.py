from fastapi import Depends, HTTPException

from features.auth.guards import get_current_user

from .models import *

__all__ = ["active_user", "get_current_user"]


def active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user
