from typing import Literal

from pydantic import BaseModel, Field

from core import *

SeatStatus = Literal["available", "held", "sold", "unavailable"]


class SeatResponse(BaseModel):
    id: str
    number: int
    accessible: bool
    status: SeatStatus


class SeatRowResponse(BaseModel):
    label: str
    seats: list[SeatResponse]


class SeatSectionResponse(BaseModel):
    """Sections come nearest tier first, then left to right, as seen with the stage on top.
    Rows come nearest the stage first and seats left to right."""

    key: str
    name: str
    tier: str
    column: int
    category: int
    rows: list[SeatRowResponse]


class SeatCategoryResponse(BaseModel):
    category: int
    name: str
    seat_count: int
    # The ticket type that sells this category; None until the organizer prices it.
    ticket_type_id: UUID | None
    ticket_type_name: str | None
    price: int | None
    max_per_order: int | None


class SeatMapResponse(BaseModel):
    layout_key: str
    name: str
    hold_minutes: int
    categories: list[SeatCategoryResponse]
    sections: list[SeatSectionResponse]


class SeatCategoryPrice(BaseModel):
    category: int
    name: str = Field(min_length=1, max_length=255)
    price: int = Field(ge=0)


class SeatingSetupRequest(BaseModel):
    """Prices each category of the venue layout; one ticket type per category."""

    categories: list[SeatCategoryPrice] = Field(min_length=1)
