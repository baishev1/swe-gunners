from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class AuditLog(DbBase):
    event_id: Mapped[UUID | None] = mapped_column(ForeignKey("event.id"), default=None)
    # TODO: point at user.id once features/users is merged
    actor_id: Mapped[UUID | None] = mapped_column(default=None)
    action: Mapped[str] = mapped_column(String(50))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[UUID]
    description: Mapped[str] = mapped_column(String(500))
