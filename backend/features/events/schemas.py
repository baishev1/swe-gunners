from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *
from features.venues.schemas import VenueResponse


class EventBase(BaseModel):
    title: str
    description: str | None = None
    category: str
    venue_id: UUID
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Almaty"
    capacity: int
    visibility: str = "public"
    is_assigned_seating: bool = False
    registration_start_time: datetime | None = None
    registration_end_time: datetime | None = None
    cover_image_url: str | None = None
    refund_policy: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    venue_id: UUID | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    capacity: int | None = None
    visibility: str | None = None
    is_assigned_seating: bool | None = None
    registration_start_time: datetime | None = None
    registration_end_time: datetime | None = None
    cover_image_url: str | None = None
    refund_policy: str | None = None


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizer_id: UUID
    status: str
    venue: VenueResponse
    created_at: datetime
    updated_at: datetime


class OrganizerDashboardResponse(BaseModel):
    upcoming: list[EventResponse]
    active: list[EventResponse]
    completed: list[EventResponse]
    cancelled: list[EventResponse]


class EventAccessLinkResponse(BaseModel):
    """Shareable link for a private event; only its organizer can read it."""

    link: str
