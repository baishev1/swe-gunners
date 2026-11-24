from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class SeatHold(DbBase):
    """One seat taken for one event: held while its order is pending, sold once paid.

    The unique (event, seat) pair is what makes double-selling impossible (SRS 4.3.1): two
    checkouts racing for the same seat both try to insert, and the database rejects one.
    A seat becomes free again by deleting its row (expired, cancelled or refunded order).
    """

    __table_args__ = (UniqueConstraint("event_id", "seat_id"),)

    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"), index=True)
    seat_id: Mapped[str] = mapped_column(String(32))
    order_id: Mapped[UUID] = mapped_column(ForeignKey("order.id", ondelete="CASCADE"), index=True)
    ticket_type_id: Mapped[UUID]
    status: Mapped[str] = mapped_column(String(10), default="held")
