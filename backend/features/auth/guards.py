import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from core import *
from features.users.models import User

from .schemas import *
from .service import auth_service

bearer = HTTPBearer(auto_error=False)


def unique_email_guard(data: RegisterRequest, db: Session = Depends(get_db)) -> RegisterRequest:
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return data


def valid_credentials_guard(data: LoginRequest, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == data.email))
    if not user or not auth_service.verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    try:
        user_id = auth_service.decode_access_token(credentials.credentials)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized from None
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise unauthorized
    return user


def require_role(*roles: str):
    def role_guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return role_guard
