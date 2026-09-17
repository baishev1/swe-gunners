from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class EventBase(BaseModel):
    title: str
    description: str | None = None
    category: str
    venue_name: str
    venue_address: str
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Almaty"
    capacity: int
    visibility: str = "public"
    is_assigned_seating: bool = False
    registration_start_time: datetime | None = None
    registration_end_time: datetime | None = None
    cover_image_url: str | None = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    venue_name: str | None = None
    venue_address: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    capacity: int | None = None
    visibility: str | None = None
    is_assigned_seating: bool | None = None
    registration_start_time: datetime | None = None
    registration_end_time: datetime | None = None
    cover_image_url: str | None = None


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organizer_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
