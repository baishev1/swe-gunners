from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class SupportCase(DbBase):
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("event.id"), index=True)
    assignee_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), default=None)
    target: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30))
    subject: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="open")


class SupportMessage(DbBase):
    case_id: Mapped[UUID] = mapped_column(ForeignKey("support_case.id"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    body: Mapped[str] = mapped_column(Text)
