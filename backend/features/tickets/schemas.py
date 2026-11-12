from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    order_item_id: UUID
    event_id: UUID
    ticket_type_id: UUID
    ticket_type_name: str
    attendee_name: str
    attendee_email: str
    qr_token: str
    status: str
    checked_in_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EventAttendeeResponse(BaseModel):
    ticket_id: UUID
    order_id: UUID
    attendee_name: str
    attendee_email: str
    ticket_type_id: UUID
    ticket_type_name: str
    ticket_status: str
    order_status: str
    checked_in_at: datetime | None = None
    created_at: datetime


class TicketVerificationResponse(BaseModel):
    valid: bool
    status: str
    ticket: TicketResponse | None = None
    message: str
