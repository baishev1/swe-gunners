from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizerProfileUpdate(BaseModel):
    organization_name: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)
    payout_recipient_name: str | None = Field(default=None, max_length=255)
    payout_iban: str | None = Field(default=None, max_length=34)
    payout_bin: str | None = Field(default=None, max_length=12)


class OrganizerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_name: str | None
    contact_email: str | None
    contact_phone: str | None
    payout_recipient_name: str | None
    payout_iban: str | None
    payout_bin: str | None
    identity_verified_at: datetime | None
    has_payout_account: bool
