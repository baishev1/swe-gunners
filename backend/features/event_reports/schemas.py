from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from core import *

ReportCategory = Literal["fraud", "inappropriate", "misleading", "other"]
ReportStatus = Literal["open", "reviewed"]


class EventReportCreate(BaseModel):
    category: ReportCategory
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ReportedEvent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str


class Reporter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str


class EventReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: ReportCategory
    reason: str
    status: ReportStatus
    event: ReportedEvent
    reporter: Reporter
    created_at: datetime
