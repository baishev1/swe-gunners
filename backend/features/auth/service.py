from datetime import timedelta

import jwt
from pwdlib import PasswordHash

from core import *
from features.users.models import User

hasher = PasswordHash.recommended()


class AuthService:
    def register(self, db: Session, email: str, password: str, full_name: str, role: str) -> User:
        from features.organizers.models import OrganizerProfile

        user = User(
            email=email, password_hash=hasher.hash(password), full_name=full_name, role=role
        )
        db.add(user)
        if role == "organizer":
            db.flush()
            db.add(OrganizerProfile(user_id=user.id))
        db.commit()
        db.refresh(user)
        return user

    def verify_password(self, password: str, password_hash: str) -> bool:
        return hasher.verify(password, password_hash)

    def create_access_token(self, user: User) -> str:
        expires = time_now() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": str(user.id), "exp": expires}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> UUID:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return UUID(payload["sub"])


auth_service = AuthService()
