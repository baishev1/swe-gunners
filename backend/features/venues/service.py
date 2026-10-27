from sqlalchemy import select

from core import *

from .models import *
from .schemas import *


class VenueService:
    def create_venue(self, db: Session, data: VenueCreate) -> Venue:
        venue = Venue(**data.model_dump())
        db.add(venue)
        db.commit()
        db.refresh(venue)
        return venue

    def list_venues(self, db: Session) -> list[Venue]:
        stmt = select(Venue).order_by(Venue.name.asc())
        return list(db.scalars(stmt).all())


venue_service = VenueService()
