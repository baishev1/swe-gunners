from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class Payment(DbBase):
    order_id: Mapped[UUID]
    amount_kzt: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(50), default="simulation")
    transaction_id: Mapped[str] = mapped_column(String(100))
