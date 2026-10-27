from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class OrganizerProfile(DbBase):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), unique=True)
    organization_name: Mapped[str | None] = mapped_column(String(255), default=None)
    contact_email: Mapped[str | None] = mapped_column(String(255), default=None)
    contact_phone: Mapped[str | None] = mapped_column(String(50), default=None)
