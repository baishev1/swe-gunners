from datetime import datetime

from pydantic import BaseModel, ConfigDict

from core import *


class PaymentSimulateRequest(BaseModel):
    order_id: UUID
    simulate_failure: bool = False


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    amount_kzt: int
    status: str
    provider: str
    transaction_id: str
    created_at: datetime
    updated_at: datetime
