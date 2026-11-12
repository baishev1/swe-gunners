from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from core import *

SupportStatus = Literal["open", "in_progress", "waiting_for_customer", "resolved"]
SupportCategory = Literal[
    "ticket_delivery",
    "payment",
    "refund",
    "seating",
    "event_information",
    "check_in",
    "account",
    "activation",
    "technical",
]
MessageBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
]


class SupportCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: Literal["organizer", "platform"]
    event_id: UUID | None = None
    category: SupportCategory
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    message: MessageBody

    @model_validator(mode="after")
    def require_event_for_organizer(self) -> "SupportCaseCreate":
        if self.target == "organizer" and self.event_id is None:
            raise ValueError("An organizer support case requires an event_id")
        return self


class SupportMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: MessageBody


class SupportStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SupportStatus


class SupportCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester_id: UUID
    event_id: UUID | None
    assignee_id: UUID | None
    target: Literal["organizer", "platform"]
    category: SupportCategory
    subject: str
    status: SupportStatus
    created_at: datetime
    updated_at: datetime


class SupportMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
