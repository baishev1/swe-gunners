from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class Ticket(DbBase):
    order_id: Mapped[UUID]
    order_item_id: Mapped[UUID]
    event_id: Mapped[UUID]
    ticket_type_id: Mapped[UUID]
    ticket_type_name: Mapped[str] = mapped_column(String(255))
    attendee_name: Mapped[str] = mapped_column(String(255))
    attendee_email: Mapped[str] = mapped_column(String(255))
    qr_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="valid")
    checked_in_at: Mapped[AwareDateTime | None] = mapped_column(default=None)
