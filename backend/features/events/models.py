import secrets

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.venues.models import Venue


class Event(DbBase):
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    category: Mapped[str] = mapped_column(String(100))
    venue_id: Mapped[UUID] = mapped_column(ForeignKey("venue.id"))
    start_time: Mapped[AwareDateTime]
    end_time: Mapped[AwareDateTime]
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Almaty")
    capacity: Mapped[int] = mapped_column(Integer)
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    registration_start_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    registration_end_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    organizer_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    is_assigned_seating: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), default=None)
    refund_policy: Mapped[str | None] = mapped_column(Text, default=None)
    # What an admin suspension replaced, so a mistaken suspension can be undone (SRS 4.12).
    status_before_suspension: Mapped[str | None] = mapped_column(String(20), default=None)
    # Secret for the shareable link of a private event (SRS 4.2); never sent to attendees.
    access_token: Mapped[str | None] = mapped_column(
        String(64), default=lambda: secrets.token_urlsafe(24), index=True
    )

    venue: Mapped[Venue] = relationship(lazy="joined")
