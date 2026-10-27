from fastapi import APIRouter, Depends, status

from core import *
from features.auth.guards import require_role
from features.users.models import User

from .models import *
from .schemas import *
from .service import venue_service

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.post("", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(
    data: VenueCreate,
    _: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return venue_service.create_venue(db=db, data=data)


@router.get("", response_model=list[VenueResponse])
def list_venues(db: Session = Depends(get_db)):
    return venue_service.list_venues(db=db)
