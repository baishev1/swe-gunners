from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.events.models import Event
from features.users.models import User


class EventReport(DbBase):
    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"), index=True)
    reporter_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    category: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="open")

    event: Mapped[Event] = relationship(lazy="joined")
    reporter: Mapped[User] = relationship(lazy="joined")
