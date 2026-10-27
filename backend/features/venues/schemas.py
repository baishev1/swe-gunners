from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class VenueBase(BaseModel):
    name: str
    address: str


class VenueCreate(VenueBase):
    pass


class VenueResponse(VenueBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
