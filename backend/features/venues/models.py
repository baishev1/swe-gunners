from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class Venue(DbBase):
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
