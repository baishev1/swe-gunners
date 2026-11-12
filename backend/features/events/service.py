from datetime import datetime

from sqlalchemy import select

from core import *
from features.audit_log.service import audit_log_service
from features.notifications.service import notification_service
from features.orders.models import Order

from .models import *
from .schemas import *


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
        for key, value in update_data.items():
            setattr(event, key, value)
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
        return event

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
        emails = list(
            db.scalars(
                select(Order.customer_email)
                .where(
                    Order.event_id == event.id,
                    Order.status.in_(("paid", "pending")),
                )
                .distinct()
            )
        )
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
