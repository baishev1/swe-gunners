import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from core import *
from features.auth.guards import bearer, get_current_user
from features.auth.service import auth_service

from .models import *

__all__ = ["active_user", "get_current_user", "optional_user"]


def active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = auth_service.decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user
