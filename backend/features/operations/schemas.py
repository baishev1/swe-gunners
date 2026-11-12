from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from core import *

ReportKind = Literal["orders", "payments", "events", "users"]


class AdminOrderResponse(BaseModel):
    id: UUID
    event_id: UUID
    event_title: str | None
    user_id: UUID | None
    customer_name: str
    customer_email: str
    total_amount_kzt: int
    status: str
    created_at: datetime


class AdminPaymentResponse(BaseModel):
    id: UUID
    order_id: UUID
    amount_kzt: int
    status: str
    provider: str
    transaction_id: str
    customer_email: str | None
    event_title: str | None
    created_at: datetime


class AdminMonitoringResponse(BaseModel):
    """Payment health for SRS 4.12. Amounts are KZT minor units (tiyn)."""

    failed_payments: int
    refunded_orders: int
    refunded_amount_kzt: int
    cancelled_orders: int
    pending_orders: int
    recent_failed_payments: list[AdminPaymentResponse]
    recent_refunds: list[AdminOrderResponse]
