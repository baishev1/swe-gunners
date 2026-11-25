import logging
import smtplib
from datetime import timedelta
from email.message import EmailMessage

import jwt
from pwdlib import PasswordHash
from sqlalchemy import func, select

from core import *
from features.users.models import User

hasher = PasswordHash.recommended()
logger = logging.getLogger(__name__)

VERIFY_TOKEN_EXPIRE = timedelta(hours=24)
RESET_TOKEN_EXPIRE = timedelta(minutes=30)


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
        self.send_verification_email(user)
        return user

    def verify_password(self, password: str, password_hash: str) -> bool:
        return hasher.verify(password, password_hash)

    def create_access_token(self, user: User) -> str:
        expires = time_now() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": str(user.id), "exp": expires}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> UUID:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if "purpose" in payload:
            raise jwt.InvalidTokenError("Expected an access token")
        return UUID(payload["sub"])

    def create_refresh_token(self, user: User) -> str:
        expires = time_now() + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": str(user.id), "purpose": "refresh", "exp": expires}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def create_verify_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "purpose": "verify",
            "exp": time_now() + VERIFY_TOKEN_EXPIRE,
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def create_reset_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "purpose": "reset",
            "pwd": user.password_hash[-10:],
            "exp": time_now() + RESET_TOKEN_EXPIRE,
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def decode_purpose_token(self, token: str, purpose: str) -> dict:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload["purpose"] != purpose:
            raise ValueError("Wrong token purpose")
        return payload

    def send_email(self, to: str, subject: str, body: str) -> None:
        if not settings.SMTP_HOST:
            logger.info("Email to %s: %s\n%s", to, subject, body)
            return
        message = EmailMessage()
        message["From"] = settings.MAIL_FROM
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        # A timeout keeps an unreachable SMTP server from hanging the request.
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USER:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)

    def send_verification_email(self, user: User) -> None:
        link = f"{settings.FRONTEND_URL}/verify-email?token={self.create_verify_token(user)}"
        self.send_email(user.email, "Confirm your email", f"Confirm your email: {link}")

    def send_password_reset_email(self, user: User) -> None:
        link = f"{settings.FRONTEND_URL}/reset-password?token={self.create_reset_token(user)}"
        self.send_email(user.email, "Reset your password", f"Reset your password: {link}")

    def verify_email(self, db: Session, user: User) -> User:
        user.is_email_verified = True
        db.commit()
        db.refresh(user)
        return user

    def request_password_reset(self, db: Session, email: str) -> None:
        user = db.scalar(select(User).where(func.lower(User.email) == email))
        if user and user.is_active:
            self.send_password_reset_email(user)

    def reset_password(self, db: Session, user: User, new_password: str) -> None:
        user.password_hash = hasher.hash(new_password)
        db.commit()


auth_service = AuthService()
