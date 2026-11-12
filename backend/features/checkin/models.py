from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class StaffAssignment(DbBase):
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)

    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)
    can_undo_check_in: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_support: Mapped[bool] = mapped_column(Boolean, default=False)
