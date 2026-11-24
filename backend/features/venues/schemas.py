from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from core import *
from features.seating.layouts import LAYOUTS


class VenueBase(BaseModel):
    name: str
    address: str


class VenueCreate(VenueBase):
    # One of the predefined seating layouts (SRS 4.3.1); there is no layout editor.
    layout_key: str | None = None

    @field_validator("layout_key")
    @classmethod
    def known_layout(cls, value: str | None) -> str | None:
        if value is not None and value not in LAYOUTS:
            raise ValueError("Unknown seating layout")
        return value


class VenueResponse(VenueBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    layout_key: str | None = None
    created_at: datetime
    updated_at: datetime
