from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from core import *
from features.audit_log.service import audit_log_service
from features.notifications.service import notification_service
from features.orders.models import Order

from .models import *
from .schemas import *

# Changes to these fields affect people who already hold tickets, so they get an email.
ATTENDEE_FACING_FIELDS = ("title", "start_time", "end_time", "venue_id", "timezone")


class EventService:
    def create_event(
        self,
        db: Session,
        data: EventCreate,
        organizer_id: UUID,
    ) -> Event:
        event = Event(**data.model_dump(), organizer_id=organizer_id)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def update_event(
        self, db: Session, event: Event, data: EventUpdate, actor_id: UUID | None = None
    ) -> Event:
        update_data = data.model_dump(exclude_unset=True)
        old_capacity = event.capacity
        old_details = {field: getattr(event, field) for field in ATTENDEE_FACING_FIELDS}
        old_venue_name = event.venue.name if event.venue else None
        for key, value in update_data.items():
            setattr(event, key, value)
        changed = [f for f in ATTENDEE_FACING_FIELDS if getattr(event, f) != old_details[f]]
        if event.capacity != old_capacity:
            self._record(
                db,
                event,
                "event_capacity_changed",
                f"Changed capacity from {old_capacity} to {event.capacity}",
                actor_id,
            )
        db.commit()
        db.refresh(event)
        if changed and event.status == "published":
            self._notify_ticket_holders_of_update(db, event, changed, old_details, old_venue_name)
        return event

    def _notify_ticket_holders_of_update(
        self,
        db: Session,
        event: Event,
        changed: list[str],
        old_details: dict[str, object],
        old_venue_name: str | None,
    ) -> None:
        """Emails holders of confirmed orders when date, time, venue or title change (SRS 4.10)."""
        lines: list[str] = []
        for field in changed:
            if field == "venue_id":
                lines.append(f"Venue: {old_venue_name or '-'} -> {event.venue.name}")
            elif field in ("start_time", "end_time"):
                label = "Starts" if field == "start_time" else "Ends"
                lines.append(f"{label}: {self._local(event, getattr(event, field))}")
            elif field == "timezone":
                lines.append(f"Time zone: {event.timezone}")
            else:
                lines.append(f"Title: {old_details[field]} -> {event.title}")
        emails = list(
            db.scalars(
                select(Order.customer_email)
                .where(Order.event_id == event.id, Order.status == "paid")
                .distinct()
            )
        )
        if emails:
            notification_service.event_updated(event.title, lines, emails)

    def _local(self, event: Event, value: datetime) -> str:
        try:
            zone = ZoneInfo(event.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            zone = ZoneInfo(settings.DEFAULT_TIMEZONE)
        return value.astimezone(zone).strftime(f"%d.%m.%Y %H:%M ({zone.key})")

    def publish_event(self, db: Session, event: Event, actor_id: UUID | None = None) -> Event:
        event.status = "published"
        self._record(db, event, "event_published", f"Published event {event.title}", actor_id)
        db.commit()
        db.refresh(event)
        return event

    def unpublish_event(self, db: Session, event: Event, actor_id: UUID | None = None) -> Event:
        event.status = "unpublished"
        self._record(db, event, "event_unpublished", f"Unpublished event {event.title}", actor_id)
        db.commit()
        db.refresh(event)
        return event

    def cancel_event(self, db: Session, event: Event, actor_id: UUID | None = None) -> Event:
        # Imported here to avoid a cycle: orders imports the events models.
        from features.orders.service import order_service

        open_orders = list(
            db.scalars(
                select(Order).where(
                    Order.event_id == event.id,
                    Order.status.in_(("paid", "pending")),
                )
            )
        )
        emails = sorted({order.customer_email for order in open_orders})
        # The platform refund policy promises a full refund when an event is cancelled.
        for order in open_orders:
            if order.status == "paid" and order.total_amount_kzt > 0:
                order_service.refund_order(db, order, actor_id)
            else:
                order_service.cancel_order(db, order, actor_id)
        event.status = "cancelled"
        self._record(db, event, "event_cancelled", f"Cancelled event {event.title}", actor_id)
        db.commit()
        db.refresh(event)
        notification_service.event_cancelled(event.title, emails)
        return event

    def duplicate_event(self, db: Session, event: Event, actor_id: UUID | None = None) -> Event:
        new_event = Event(
            title=f"{event.title} (Copy)",
            description=event.description,
            category=event.category,
            venue_id=event.venue_id,
            start_time=event.start_time,
            end_time=event.end_time,
            timezone=event.timezone,
            capacity=event.capacity,
            visibility=event.visibility,
            status="draft",
            organizer_id=event.organizer_id,
            is_assigned_seating=event.is_assigned_seating,
            cover_image_url=event.cover_image_url,
            refund_policy=event.refund_policy,
        )
        db.add(new_event)
        db.flush()
        self._record(
            db, event, "event_duplicated", f"Duplicated into draft {new_event.title}", actor_id
        )
        self._record(
            db, new_event, "event_created", f"Created as a copy of {event.title}", actor_id
        )
        db.commit()
        db.refresh(new_event)
        return new_event

    def list_events(self, db: Session) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.status == "published", Event.visibility == "public")
            .order_by(Event.start_time.asc())
        )
        return list(db.scalars(stmt).all())

    def list_organizer_events(
        self, db: Session, organizer_id: UUID, status: str | None = None
    ) -> list[Event]:
        stmt = select(Event).where(Event.organizer_id == organizer_id)
        if status:
            stmt = stmt.where(Event.status == status)
        stmt = stmt.order_by(Event.start_time.asc())
        return list(db.scalars(stmt).all())

    def event_phase(self, event: Event, now: datetime) -> str:
        """Dashboard bucket for SRS 4.16: upcoming, active, completed or cancelled.

        Suspended events cannot sell or admit anyone, so they sit with cancelled ones.
        Drafts are grouped by date like any other event.
        """
        if event.status in ("cancelled", "suspended"):
            return "cancelled"
        if now < event.start_time:
            return "upcoming"
        if now < event.end_time:
            return "active"
        return "completed"

    def organizer_dashboard(self, db: Session, organizer_id: UUID) -> dict[str, list[Event]]:
        now = time_now()
        phases: dict[str, list[Event]] = {
            "upcoming": [],
            "active": [],
            "completed": [],
            "cancelled": [],
        }
        for event in self.list_organizer_events(db, organizer_id):
            phases[self.event_phase(event, now)].append(event)
        # Past events read best newest first.
        phases["completed"].reverse()
        phases["cancelled"].reverse()
        return phases

    def calendar_file(self, event: Event) -> str:
        """iCalendar export (SRS 4.11). The UID never changes and SEQUENCE grows with every
        update, so re-importing the file replaces the earlier entry instead of adding one."""
        status = "CANCELLED" if event.status == "cancelled" else "CONFIRMED"
        title = f"Cancelled: {event.title}" if status == "CANCELLED" else event.title
        url = f"{settings.FRONTEND_URL}/events/detail?event_id={event.id}"
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//BiletFlow//Events//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-TIMEZONE:{event.timezone}",
            "BEGIN:VEVENT",
            f"UID:{event.id}@biletflow",
            f"SEQUENCE:{int(event.updated_at.timestamp())}",
            f"DTSTAMP:{self._ics_time(event.updated_at)}",
            f"DTSTART:{self._ics_time(event.start_time)}",
            f"DTEND:{self._ics_time(event.end_time)}",
            f"SUMMARY:{self._ics_text(title)}",
            f"DESCRIPTION:{self._ics_text(event.description or '')}",
            f"LOCATION:{self._ics_text(f'{event.venue.name}, {event.venue.address}')}",
            f"URL:{url}",
            f"STATUS:{status}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]
        return "".join(self._ics_fold(line) + "\r\n" for line in lines)

    def _ics_time(self, value: datetime) -> str:
        return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")

    def _ics_text(self, value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\r\n", "\\n")
            .replace("\n", "\\n")
        )

    def _ics_fold(self, line: str) -> str:
        # RFC 5545 caps content lines at 75 octets; longer ones continue after CRLF + space.
        parts = []
        chunk = ""
        for char in line:
            if len((chunk + char).encode()) > 74:
                parts.append(chunk)
                chunk = ""
            chunk += char
        parts.append(chunk)
        return "\r\n ".join(parts)

    def _record(
        self, db: Session, event: Event, action: str, description: str, actor_id: UUID | None
    ) -> None:
        audit_log_service.record(
            db,
            action=action,
            entity_type="event",
            entity_id=event.id,
            description=description,
            event_id=event.id,
            actor_id=actor_id,
        )


event_service = EventService()
