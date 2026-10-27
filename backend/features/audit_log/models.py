from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.users.models import User


class AuditLog(DbBase):
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("event.id"), default=None)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("user.id"), default=None)
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[UUID]
    description: Mapped[str] = mapped_column(String(500))

    actor: Mapped[User | None] = relationship(lazy="joined")

    @property
    def actor_name(self) -> str | None:
        return self.actor.full_name if self.actor else None
