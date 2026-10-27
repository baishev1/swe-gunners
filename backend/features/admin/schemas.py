from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core import *


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_email_verified: bool
    created_at: datetime


class PlatformSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activation_fee: int
    updated_at: datetime


class PlatformSettingUpdate(BaseModel):
    activation_fee: int = Field(ge=0)
