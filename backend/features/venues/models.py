from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class Venue(DbBase):
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
    # Predefined seating layout of this venue (SRS 4.3.1); None for general admission only.
    layout_key: Mapped[str | None] = mapped_column(String(50), default=None)
