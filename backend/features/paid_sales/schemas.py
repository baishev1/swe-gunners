from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core import *


class ActivationFeePaymentRequest(BaseModel):
    simulate_failure: bool = False


class PaidSalesSuspendRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class PaidSalesChecklistResponse(BaseModel):
    event_id: UUID
    status: str
    fee_amount: int
    fee_transaction_id: str | None
    fee_paid_at: datetime | None
    terms_accepted_at: datetime | None
    activated_at: datetime | None
    suspended_at: datetime | None
    suspension_reason: str | None
    has_paid_ticket_type: bool
    identity_verified: bool
    payout_account_ready: bool
    fee_paid: bool
    terms_accepted: bool
    can_activate: bool


class PaidSalesActivationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    event_title: str
    status: str
    fee_amount: int | None
    fee_transaction_id: str | None
    fee_paid_at: datetime | None
    terms_accepted_at: datetime | None
    activated_at: datetime | None
    suspended_at: datetime | None
    suspension_reason: str | None
    created_at: datetime
    updated_at: datetime
