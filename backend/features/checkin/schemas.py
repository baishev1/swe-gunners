from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class StaffAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    can_undo_check_in: bool = False
    can_manage_support: bool = False


class StaffAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    user_id: UUID
    can_undo_check_in: bool
    can_manage_support: bool
    created_at: datetime
    updated_at: datetime
