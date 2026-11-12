from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class PlatformSetting(DbBase):
    """Single row of platform-wide settings edited by platform admins."""

    # Paid Sales Activation Fee per event, in tiyn.
    activation_fee: Mapped[int] = mapped_column(Integer, default=0)
    # Share of net sales kept as a simulated processing charge, in percent.
    processing_fee_percent: Mapped[float] = mapped_column(Float, default=3.0)
