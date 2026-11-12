from datetime import date

from pydantic import BaseModel

from core import *


class CapacitySummary(BaseModel):
    total_capacity: int
    tickets_sold: int
    tickets_remaining: int
    percent_sold: float


class RevenueSummary(BaseModel):
    """All amounts are KZT minor units (tiyn)."""

    gross_sales: int
    discounts: int
    refunds: int
    net_revenue: int


class SalesPoint(BaseModel):
    day: date
    orders: int
    tickets: int
    gross_sales: int


class TicketTypeSales(BaseModel):
    ticket_type_id: UUID
    name: str
    price: int
    capacity: int
    tickets_sold: int
    gross_sales: int
    checked_in: int


class CampaignSales(BaseModel):
    campaign_id: UUID
    name: str
    code: str
    is_disabled: bool
    redemptions: int
    tickets: int
    discounts: int
    revenue: int


class AttendanceSummary(BaseModel):
    checked_in: int
    absent: int
    percent_checked_in: float


class EventAnalyticsResponse(BaseModel):
    event_id: UUID
    capacity: CapacitySummary
    revenue: RevenueSummary
    sales_over_time: list[SalesPoint]
    ticket_types: list[TicketTypeSales]
    campaigns: list[CampaignSales]
    attendance: AttendanceSummary
