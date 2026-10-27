from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core import *


class TicketTypeBase(BaseModel):
    name: str
    description: str | None = None
    price: int = Field(default=0, ge=0)
    quantity: int = Field(gt=0)
    max_per_order: int | None = Field(default=None, gt=0)
    sales_start_time: datetime | None = None
    sales_end_time: datetime | None = None
    is_hidden: bool = False


class TicketTypeCreate(TicketTypeBase):
    pass


class TicketTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, gt=0)
    max_per_order: int | None = Field(default=None, gt=0)
    sales_start_time: datetime | None = None
    sales_end_time: datetime | None = None
    is_hidden: bool | None = None


class TicketTypeResponse(TicketTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    reserved_count: int
    sold_count: int
    available: int
    created_at: datetime
    updated_at: datetime
