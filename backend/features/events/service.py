from sqlalchemy import select

from core import *

from .models import *
from .schemas import *


class EventService:
    def create_event(
        self,
        db: Session,
        data: EventCreate,
        organizer_id: UUID | None = None,
    ) -> Event:
        payload = data.model_dump()
        if organizer_id:
            payload["organizer_id"] = organizer_id
        event = Event(**payload)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def update_event(self, db: Session, event: Event, data: EventUpdate) -> Event:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        db.commit()
        db.refresh(event)
        return event

    def publish_event(self, db: Session, event: Event) -> Event:
        event.status = "published"
        db.commit()
        db.refresh(event)
        return event

    def unpublish_event(self, db: Session, event: Event) -> Event:
        event.status = "unpublished"
        db.commit()
        db.refresh(event)
        return event

    def cancel_event(self, db: Session, event: Event) -> Event:
        event.status = "cancelled"
        db.commit()
        db.refresh(event)
        return event

    def duplicate_event(self, db: Session, event: Event) -> Event:
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
        db.commit()
        db.refresh(new_event)
        return new_event

    def list_events(
        self,
        db: Session,
        organizer_id: UUID | None = None,
        status: str | None = None,
    ) -> list[Event]:
        stmt = select(Event)
        if organizer_id:
            stmt = stmt.where(Event.organizer_id == organizer_id)
        if status:
            stmt = stmt.where(Event.status == status)
        elif not organizer_id:
            stmt = stmt.where(Event.status == "published", Event.visibility == "public")
        stmt = stmt.order_by(Event.start_time.asc())
        return list(db.scalars(stmt).all())


event_service = EventService()
