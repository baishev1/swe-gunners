from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class Event(DbBase):
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    category: Mapped[str] = mapped_column(String(100))
    venue_name: Mapped[str] = mapped_column(String(255))
    venue_address: Mapped[str] = mapped_column(String(500))
    start_time: Mapped[AwareDateTime]
    end_time: Mapped[AwareDateTime]
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Almaty")
    capacity: Mapped[int] = mapped_column(Integer)
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    registration_start_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    registration_end_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    organizer_id: Mapped[UUID] = mapped_column(default=uuid7)
    is_assigned_seating: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), default=None)
