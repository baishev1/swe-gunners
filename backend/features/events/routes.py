from fastapi import APIRouter, Depends, status

from core import *

from .guards import *
from .models import *
from .schemas import *
from .service import event_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate = Depends(valid_event_create),
    organizer_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return event_service.create_event(db=db, data=data, organizer_id=organizer_id)


@router.get("", response_model=list[EventResponse])
def list_events(
    organizer_id: UUID | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return event_service.list_events(db=db, organizer_id=organizer_id, status=status)


@router.get("/detail", response_model=EventResponse)
def get_event_detail(event: Event = Depends(valid_event_id)):
    return event


@router.patch("/update", response_model=EventResponse)
def update_event(
    data: EventUpdate = Depends(valid_event_update),
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
):
    return event_service.update_event(db=db, event=event, data=data)


@router.post("/publish", response_model=EventResponse)
def publish_event(
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
):
    return event_service.publish_event(db=db, event=event)


@router.post("/unpublish", response_model=EventResponse)
def unpublish_event(
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
):
    return event_service.unpublish_event(db=db, event=event)


@router.post("/cancel", response_model=EventResponse)
def cancel_event(
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
):
    return event_service.cancel_event(db=db, event=event)


@router.post("/duplicate", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def duplicate_event(
    event: Event = Depends(valid_event_id),
    db: Session = Depends(get_db),
):
    return event_service.duplicate_event(db=db, event=event)
