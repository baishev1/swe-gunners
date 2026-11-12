from dataclasses import dataclass, field
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from core import *
from features.admin.service import admin_service
from features.events.models import Event
from features.orders.models import Order
from features.promo.models import PromoCampaign, PromoRedemption
from features.ticket_types.models import TicketType
from features.tickets.models import Ticket

from .schemas import *

# Orders that took money at some point. Refunded ones count toward gross sales and
# then come back out as refunds, so net revenue reflects what the organizer keeps.
SOLD_ORDER_STATUSES = ("paid", "refunded")


@dataclass
class _TicketTypeTotals:
    name: str
    price: int = 0
    capacity: int = 0
    tickets_sold: int = 0
    gross_sales: int = 0
    checked_in: int = 0


@dataclass
class _DayTotals:
    orders: int = 0
    tickets: int = 0
    gross_sales: int = 0


@dataclass
class _CampaignTotals:
    campaign: PromoCampaign
    redemptions: int = 0
    tickets: int = 0
    discounts: int = 0
    revenue: int = 0


@dataclass
class _OrderLine:
    """The part of one order that passes the ticket type filter."""

    order: Order
    subtotal: int
    tickets: int
    discount: int
    quantities: dict[UUID, int] = field(default_factory=dict)
    amounts: dict[UUID, int] = field(default_factory=dict)


class AnalyticsService:
    def event_analytics(
        self,
        db: Session,
        event: Event,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket_type_id: UUID | None = None,
    ) -> EventAnalyticsResponse:
        """Builds the organizer dashboard from order, ticket, promo and check-in records.

        Read-only and computed on request, so it never touches checkout state.
        """
        ticket_types = self._ticket_types(db, event.id, ticket_type_id)
        lines = self._order_lines(db, event.id, date_from, date_to, ticket_type_id)
        paid_lines = [line for line in lines if line.order.status == "paid"]
        tickets = self._admission_tickets(db, [line.order.id for line in paid_lines])
        if ticket_type_id:
            tickets = [ticket for ticket in tickets if ticket.ticket_type_id == ticket_type_id]

        by_type = self._ticket_type_totals(ticket_types, lines, tickets)
        tickets_sold = sum(line.tickets for line in paid_lines)
        total_capacity = sum(tt.quantity for tt in ticket_types)
        if not ticket_types and ticket_type_id is None:
            total_capacity = event.capacity

        gross = sum(line.subtotal for line in lines)
        discounts = sum(line.discount for line in lines)
        refunds = sum(
            line.subtotal - line.discount for line in lines if line.order.status == "refunded"
        )
        net_revenue = gross - discounts - refunds
        fee_percent = admin_service.get_settings(db).processing_fee_percent
        processing_fees = round(net_revenue * fee_percent / 100) if net_revenue > 0 else 0
        checked_in = sum(1 for ticket in tickets if ticket.status == "checked_in")

        return EventAnalyticsResponse(
            event_id=event.id,
            capacity=CapacitySummary(
                total_capacity=total_capacity,
                tickets_sold=tickets_sold,
                tickets_remaining=max(total_capacity - tickets_sold, 0),
                percent_sold=self._percent(tickets_sold, total_capacity),
            ),
            revenue=RevenueSummary(
                gross_sales=gross,
                discounts=discounts,
                refunds=refunds,
                net_revenue=net_revenue,
                processing_fees=processing_fees,
                estimated_payout=net_revenue - processing_fees,
            ),
            sales_over_time=self._sales_over_time(lines, self._zone(event.timezone)),
            ticket_types=[
                TicketTypeSales(ticket_type_id=type_id, **vars(totals))
                for type_id, totals in by_type.items()
            ],
            campaigns=self._campaigns(db, event.id, paid_lines),
            attendance=AttendanceSummary(
                checked_in=checked_in,
                absent=len(tickets) - checked_in,
                percent_checked_in=self._percent(checked_in, len(tickets)),
            ),
        )

    def _ticket_types(
        self, db: Session, event_id: UUID, ticket_type_id: UUID | None
    ) -> list[TicketType]:
        stmt = select(TicketType).where(TicketType.event_id == event_id)
        if ticket_type_id:
            stmt = stmt.where(TicketType.id == ticket_type_id)
        return list(db.scalars(stmt.order_by(TicketType.created_at)).all())

    def _order_lines(
        self,
        db: Session,
        event_id: UUID,
        date_from: datetime | None,
        date_to: datetime | None,
        ticket_type_id: UUID | None,
    ) -> list[_OrderLine]:
        stmt = select(Order).where(
            Order.event_id == event_id, Order.status.in_(SOLD_ORDER_STATUSES)
        )
        if date_from:
            stmt = stmt.where(Order.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Order.created_at < date_to)
        orders = list(db.scalars(stmt.order_by(Order.created_at)).all())
        if not orders:
            return []

        discounts: dict[UUID, int] = {}
        redemptions = db.scalars(
            select(PromoRedemption).where(PromoRedemption.order_id.in_([o.id for o in orders]))
        ).all()
        for redemption in redemptions:
            discounts[redemption.order_id] = (
                discounts.get(redemption.order_id, 0) + redemption.discount_amount
            )

        lines: list[_OrderLine] = []
        for order in orders:
            order_subtotal = sum(item.unit_price_kzt * item.quantity for item in order.items)
            items = [
                item
                for item in order.items
                if ticket_type_id is None or item.ticket_type_id == ticket_type_id
            ]
            if not items:
                continue
            line = _OrderLine(order=order, subtotal=0, tickets=0, discount=0)
            for item in items:
                amount = item.unit_price_kzt * item.quantity
                line.subtotal += amount
                line.tickets += item.quantity
                type_id = item.ticket_type_id
                line.quantities[type_id] = line.quantities.get(type_id, 0) + item.quantity
                line.amounts[type_id] = line.amounts.get(type_id, 0) + amount
            # A promo discount belongs to the whole order; with a ticket type filter only
            # that type's share of it is counted.
            order_discount = discounts.get(order.id, 0)
            if order_subtotal:
                line.discount = order_discount * line.subtotal // order_subtotal
            lines.append(line)
        return lines

    def _admission_tickets(self, db: Session, paid_order_ids: list[UUID]) -> list[Ticket]:
        if not paid_order_ids:
            return []
        stmt = select(Ticket).where(
            Ticket.order_id.in_(paid_order_ids),
            Ticket.status.in_(("valid", "checked_in")),
        )
        return list(db.scalars(stmt).all())

    def _ticket_type_totals(
        self,
        ticket_types: list[TicketType],
        lines: list[_OrderLine],
        tickets: list[Ticket],
    ) -> dict[UUID, _TicketTypeTotals]:
        totals = {
            tt.id: _TicketTypeTotals(name=tt.name, price=tt.price, capacity=tt.quantity)
            for tt in ticket_types
        }
        for line in lines:
            for item in line.order.items:
                if item.ticket_type_id not in line.quantities:
                    continue
                # Order items keep the ticket type name, so sales of a deleted type still
                # show up under the name the attendee bought.
                totals.setdefault(
                    item.ticket_type_id,
                    _TicketTypeTotals(name=item.ticket_type_name, price=item.unit_price_kzt),
                )
            for type_id, quantity in line.quantities.items():
                if line.order.status == "paid":
                    totals[type_id].tickets_sold += quantity
                totals[type_id].gross_sales += line.amounts[type_id]
        for ticket in tickets:
            if ticket.status == "checked_in" and ticket.ticket_type_id in totals:
                totals[ticket.ticket_type_id].checked_in += 1
        return totals

    def _sales_over_time(self, lines: list[_OrderLine], zone: ZoneInfo) -> list[SalesPoint]:
        days: dict[date, _DayTotals] = {}
        for line in lines:
            day = line.order.created_at.astimezone(zone).date()
            totals = days.setdefault(day, _DayTotals())
            totals.orders += 1
            totals.tickets += line.tickets
            totals.gross_sales += line.subtotal
        return [SalesPoint(day=day, **vars(totals)) for day, totals in sorted(days.items())]

    def _campaigns(
        self, db: Session, event_id: UUID, paid_lines: list[_OrderLine]
    ) -> list[CampaignSales]:
        campaigns = db.scalars(
            select(PromoCampaign)
            .where(PromoCampaign.event_id == event_id)
            .order_by(PromoCampaign.created_at)
        ).all()
        totals = {campaign.id: _CampaignTotals(campaign=campaign) for campaign in campaigns}
        lines_by_order = {line.order.id: line for line in paid_lines}
        if lines_by_order:
            redemptions = db.scalars(
                select(PromoRedemption).where(PromoRedemption.order_id.in_(list(lines_by_order)))
            ).all()
            for redemption in redemptions:
                campaign_totals = totals.get(redemption.campaign_id)
                if campaign_totals is None:
                    continue
                line = lines_by_order[redemption.order_id]
                campaign_totals.redemptions += 1
                campaign_totals.tickets += line.tickets
                campaign_totals.discounts += line.discount
                campaign_totals.revenue += line.subtotal - line.discount
        return [
            CampaignSales(
                campaign_id=t.campaign.id,
                name=t.campaign.name,
                code=t.campaign.code,
                is_disabled=t.campaign.is_disabled,
                redemptions=t.redemptions,
                tickets=t.tickets,
                discounts=t.discounts,
                revenue=t.revenue,
            )
            for t in totals.values()
        ]

    def _zone(self, name: str) -> ZoneInfo:
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            return ZoneInfo("UTC")

    def _percent(self, part: int, whole: int) -> float:
        return round(part * 100 / whole, 1) if whole else 0.0


analytics_service = AnalyticsService()
