from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import delete, select, update

from core import *
from features.events.models import Event
from features.orders.models import Order
from features.orders.schemas import OrderItemCreate
from features.ticket_types.models import TicketType
from features.ticket_types.schemas import TicketTypeCreate, TicketTypeUpdate
from features.ticket_types.service import ticket_type_service

from .layouts import VenueLayout, get_layout, seat_key
from .models import *
from .schemas import *


class SeatingService:
    def layout_for_event(self, event: Event) -> VenueLayout | None:
        return get_layout(event.venue.layout_key) if event.venue else None

    def seat_ticket_types(self, db: Session, event: Event) -> dict[int, TicketType]:
        """The ticket type selling each price category; the oldest one wins."""
        ticket_types = db.scalars(
            select(TicketType)
            .where(TicketType.event_id == event.id, TicketType.seat_category.is_not(None))
            .order_by(TicketType.created_at.asc())
        ).all()
        by_category: dict[int, TicketType] = {}
        for ticket_type in ticket_types:
            assert ticket_type.seat_category is not None
            by_category.setdefault(ticket_type.seat_category, ticket_type)
        return by_category

    def taken_seats(self, db: Session, event_id: UUID) -> dict[str, str]:
        """Seat id -> "held" or "sold". Holds of orders past their time limit don't count,
        even before the cleanup job has expired those orders (SRS 4.3.1)."""
        cutoff = time_now() - timedelta(minutes=settings.ORDER_HOLD_MINUTES)
        rows = db.execute(
            select(SeatHold.seat_id, SeatHold.status, Order.status, Order.created_at)
            .join(Order, Order.id == SeatHold.order_id)
            .where(SeatHold.event_id == event_id)
        ).all()
        taken: dict[str, str] = {}
        for seat_id, hold_status, order_status, created_at in rows:
            if hold_status == "sold":
                taken[seat_id] = "sold"
            elif order_status == "pending" and created_at > cutoff:
                taken[seat_id] = "held"
        return taken

    def seat_map(self, db: Session, event: Event, layout: VenueLayout) -> SeatMapResponse:
        now = time_now()
        by_category = self.seat_ticket_types(db, event)
        on_sale = {
            category
            for category, t in by_category.items()
            if not t.is_hidden
            and not (t.sales_start_time and now < t.sales_start_time)
            and not (t.sales_end_time and now > t.sales_end_time)
        }
        taken = self.taken_seats(db, event.id)

        def seat_status(seat_id: str, category: int) -> SeatStatus:
            if seat_id in taken:
                return "sold" if taken[seat_id] == "sold" else "held"
            return "available" if category in on_sale else "unavailable"

        # One view for every hall: stage on top, nearest tier and row first, seat 1 on the
        # left. A plan drawn with the stage at the bottom is turned round by 180 degrees.
        flip = layout.stage == "bottom"
        ascending = (layout.numbering == "left_to_right") != flip
        tiers = list(dict.fromkeys(section.tier for section in layout.sections))
        if flip:
            tiers.reverse()
        last_column = max(section.column for section in layout.sections)
        ordered = sorted(
            layout.sections,
            key=lambda section: (
                tiers.index(section.tier),
                last_column - section.column if flip else section.column,
            ),
        )
        sections = [
            SeatSectionResponse(
                key=section.key,
                name=section.name,
                tier=section.tier,
                column=last_column - section.column if flip else section.column,
                category=section.category,
                rows=[
                    SeatRowResponse(
                        label=row.label,
                        seats=[
                            SeatResponse(
                                id=seat.id,
                                number=seat.number,
                                accessible=seat.accessible,
                                status=seat_status(seat.id, section.category),
                            )
                            for seat in (
                                layout.seats[seat_key(section.key, row.label, n)]
                                for n in (row.numbers if ascending else reversed(row.numbers))
                            )
                        ],
                    )
                    for row in (reversed(section.rows) if flip else section.rows)
                ],
            )
            for section in ordered
        ]
        categories = [
            SeatCategoryResponse(
                category=c.category,
                name=c.name,
                seat_count=layout.seat_count(c.category),
                ticket_type_id=by_category[c.category].id if c.category in by_category else None,
                ticket_type_name=by_category[c.category].name
                if c.category in by_category
                else None,
                price=by_category[c.category].price if c.category in by_category else None,
                max_per_order=by_category[c.category].max_per_order
                if c.category in by_category
                else None,
            )
            for c in layout.categories
        ]
        return SeatMapResponse(
            layout_key=layout.key,
            name=layout.name,
            hold_minutes=settings.ORDER_HOLD_MINUTES,
            categories=categories,
            sections=sections,
        )

    def seat_selection_error(
        self,
        event: Event,
        items: Sequence[OrderItemCreate],
        ticket_types: dict[UUID, TicketType],
    ) -> str | None:
        """Checks the seats of an order against the layout; None when they're fine."""
        if not event.is_assigned_seating:
            if any(item.seats for item in items):
                return "This event does not use assigned seating"
            return None

        layout = self.layout_for_event(event)
        if layout is None:
            return "This event has no seating layout"
        chosen: set[str] = set()
        for item in items:
            ticket_type = ticket_types[item.ticket_type_id]
            if ticket_type.seat_category is None:
                return f"{ticket_type.name} does not sell seats"
            if len(item.seats) != item.quantity:
                return "Choose one seat for each ticket"
            for seat_id in item.seats:
                seat = layout.seats.get(seat_id)
                if seat is None:
                    return f"Seat {seat_id} does not exist"
                if seat.section.category != ticket_type.seat_category:
                    return f"Seat {seat_id} is not sold as {ticket_type.name}"
                if seat_id in chosen:
                    return f"Seat {seat_id} is selected twice"
                chosen.add(seat_id)
        return None

    # The three calls below run inside the order's transaction and never commit.
    def hold_seats(self, db: Session, order: Order) -> None:
        """Inserts a hold per seat. Raises IntegrityError if another order has a seat."""
        for item in order.items:
            for seat_id in item.seats:
                db.add(
                    SeatHold(
                        event_id=order.event_id,
                        seat_id=seat_id,
                        order_id=order.id,
                        ticket_type_id=item.ticket_type_id,
                        status="held",
                    )
                )
        db.flush()

    def mark_sold(self, db: Session, order: Order) -> None:
        db.execute(
            update(SeatHold)
            .where(SeatHold.order_id == order.id)
            .values(status="sold")
            .execution_options(synchronize_session=False)
        )

    def release_seats(self, db: Session, order_id: UUID) -> None:
        db.execute(
            delete(SeatHold)
            .where(SeatHold.order_id == order_id)
            .execution_options(synchronize_session=False)
        )

    def setup(
        self,
        db: Session,
        event: Event,
        layout: VenueLayout,
        data: SeatingSetupRequest,
        actor_id: UUID | None,
    ) -> list[TicketType]:
        """Creates or reprices one ticket type per category, sized to its seat count."""
        event.is_assigned_seating = True
        existing = self.seat_ticket_types(db, event)
        new_seats = sum(
            layout.seat_count(c.category) for c in data.categories if c.category not in existing
        )
        needed = ticket_type_service.total_quantity(db, event.id) + new_seats
        event.capacity = max(event.capacity, needed)
        db.commit()

        for price in data.categories:
            ticket_type = existing.get(price.category)
            if ticket_type is None:
                ticket_type = ticket_type_service.create_ticket_type(
                    db,
                    event,
                    TicketTypeCreate(
                        name=price.name,
                        price=price.price,
                        quantity=layout.seat_count(price.category),
                    ),
                    actor_id,
                )
                ticket_type.seat_category = price.category
                db.commit()
            else:
                ticket_type_service.update_ticket_type(
                    db, ticket_type, TicketTypeUpdate(name=price.name, price=price.price), actor_id
                )
        return list(self.seat_ticket_types(db, event).values())


seating_service = SeatingService()
