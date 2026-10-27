from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.events.models import Event


class TicketType(DbBase):
    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    price: Mapped[int] = mapped_column(Integer, default=0)
    quantity: Mapped[int] = mapped_column(Integer)
    max_per_order: Mapped[int | None] = mapped_column(Integer, default=None)
    sales_start_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    sales_end_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    reserved_count: Mapped[int] = mapped_column(Integer, default=0)
    sold_count: Mapped[int] = mapped_column(Integer, default=0)

    event: Mapped[Event] = relationship()

    @property
    def available(self) -> int:
        return self.quantity - self.reserved_count - self.sold_count
