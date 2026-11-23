from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *


class Order(DbBase):
    user_id: Mapped[UUID | None] = mapped_column(default=None)
    event_id: Mapped[UUID]
    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    total_amount_kzt: Mapped[int] = mapped_column(Integer, default=0)
    # Promo campaign applied at checkout (SRS 4.14); redeemed when the order is confirmed.
    promo_campaign_id: Mapped[UUID | None] = mapped_column(default=None)
    discount_kzt: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), default="pending")

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(DbBase):
    order_id: Mapped[UUID] = mapped_column(ForeignKey("order.id", ondelete="CASCADE"))
    ticket_type_id: Mapped[UUID]
    ticket_type_name: Mapped[str] = mapped_column(String(255))
    unit_price_kzt: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)

    order: Mapped["Order"] = relationship(back_populates="items")
