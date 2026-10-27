from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID | None
    actor_id: UUID | None
    actor_name: str | None
    action: str
    entity_type: str
    entity_id: UUID
    description: str
    created_at: datetime
