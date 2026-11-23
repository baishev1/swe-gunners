from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core import *
from features.events.schemas import EventResponse


class StaffAssignmentCreate(BaseModel):
    """Organizers know their staff by email; `user_id` stays for API clients and tests."""

    model_config = ConfigDict(extra="forbid")

    user_id: UUID | None = None
    email: str | None = Field(default=None, max_length=255)
    can_undo_check_in: bool = False
    can_manage_support: bool = False

    @model_validator(mode="after")
    def check_user(self) -> "StaffAssignmentCreate":
        if (self.user_id is None) == (not self.email):
            raise ValueError("Provide exactly one of user_id or email")
        return self


class StaffAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    user_id: UUID
    user_email: str
    user_full_name: str
    can_undo_check_in: bool
    can_manage_support: bool
    created_at: datetime
    updated_at: datetime


class AssignedEventResponse(EventResponse):
    can_undo_check_in: bool


class CheckInSummaryResponse(BaseModel):
    event_id: UUID
    registered: int
    checked_in: int
