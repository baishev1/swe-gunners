from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from core import *


class PromoCampaignCreate(BaseModel):
    name: str
    discount_type: Literal["percent", "fixed"]
    discount_value: int = Field(gt=0)
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    max_redemptions: int | None = Field(default=None, gt=0)
    ticket_type_ids: list[UUID] = []

    @model_validator(mode="after")
    def check_values(self) -> "PromoCampaignCreate":
        if self.discount_type == "percent" and self.discount_value > 100:
            raise ValueError("Percent discount cannot exceed 100")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class PromoCampaignUpdate(BaseModel):
    name: str | None = None
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    max_redemptions: int | None = Field(default=None, gt=0)


class PromoCampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    name: str
    code: str
    discount_type: str
    discount_value: int
    start_time: datetime | None
    end_time: datetime | None
    max_redemptions: int | None
    redemption_count: int
    is_disabled: bool
    ticket_type_ids: list[UUID]
    # The trackable HTTPS link the Campaign QR Code encodes (SRS 4.14).
    link: str
    created_at: datetime
    updated_at: datetime


class PromoCampaignPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    code: str
    discount_type: str
    discount_value: int
    end_time: datetime | None
    # Lets checkout preview the discount; the server recalculates it on the order.
    ticket_type_ids: list[UUID] = []
