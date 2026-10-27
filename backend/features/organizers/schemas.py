from pydantic import BaseModel, ConfigDict, Field


class OrganizerProfileUpdate(BaseModel):
    organization_name: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=50)


class OrganizerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_name: str | None
    contact_email: str | None
    contact_phone: str | None
