from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core import *


class OrderItemBase(BaseModel):
    ticket_type_id: UUID
    ticket_type_name: str
    unit_price_kzt: int = Field(ge=0)
    quantity: int = Field(ge=1)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    created_at: datetime
    updated_at: datetime


class OrderBase(BaseModel):
    event_id: UUID
    customer_name: str
    customer_email: str
    user_id: UUID | None = None


class OrderCreate(OrderBase):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_amount_kzt: int
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []
