from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.users.models import User


class StaffAssignment(DbBase):
    __table_args__ = (UniqueConstraint("event_id", "user_id"),)

    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), index=True)
    can_undo_check_in: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_support: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(lazy="joined")

    @property
    def user_email(self) -> str:
        return self.user.email

    @property
    def user_full_name(self) -> str:
        return self.user.full_name
