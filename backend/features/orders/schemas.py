from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, computed_field

from core import *


class OrderItemBase(BaseModel):
    ticket_type_id: UUID
    ticket_type_name: str
    unit_price_kzt: int = Field(ge=0)
    quantity: int = Field(ge=1)
    seats: list[str] = []


class OrderItemCreate(BaseModel):
    ticket_type_id: UUID
    quantity: int = Field(ge=1)
    # Required for assigned-seating events: one seat id per ticket.
    seats: list[str] = Field(default=[], max_length=50)


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


class OrderCreate(OrderBase):
    items: list[OrderItemCreate] = Field(min_length=1)
    promo_code: str | None = Field(default=None, max_length=20)
    # The secret from a private event's link (SRS 4.2).
    access_token: str | None = Field(default=None, max_length=64)


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    total_amount_kzt: int
    discount_kzt: int = 0
    promo_campaign_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hold_expires_at(self) -> datetime | None:
        """When an unpaid checkout releases its tickets; None once the order settles."""
        if self.status != "pending":
            return None
        return self.created_at + timedelta(minutes=settings.ORDER_HOLD_MINUTES)
