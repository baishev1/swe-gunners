from fastapi import APIRouter, Depends, status

from core import *
from features.auth.guards import require_role, verified_organizer_guard
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import event_service

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate = Depends(valid_event_create),
    user: User = Depends(verified_organizer_guard),
    db: Session = Depends(get_db),
):
    return event_service.create_event(db=db, data=data, organizer_id=user.id)


@router.get("", response_model=list[EventResponse])
def list_events(db: Session = Depends(get_db)):
    return event_service.list_events(db=db)


@router.get("/mine", response_model=list[EventResponse])
def list_my_events(
    status: str | None = None,
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.list_organizer_events(db=db, organizer_id=user.id, status=status)


@router.get("/dashboard", response_model=OrganizerDashboardResponse)
def get_organizer_dashboard(
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.organizer_dashboard(db=db, organizer_id=user.id)


@router.get("/detail", response_model=EventResponse)
def get_event_detail(event: Event = Depends(viewable_event_guard)):
    return event


@router.patch("/update", response_model=EventResponse)
def update_event(
    data: EventUpdate = Depends(valid_event_update),
    event: Event = Depends(owned_event_guard),
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.update_event(db=db, event=event, data=data, actor_id=user.id)


@router.post("/publish", response_model=EventResponse)
def publish_event(
    user: User = Depends(verified_organizer_guard),
    event: Event = Depends(owned_event_guard),
    db: Session = Depends(get_db),
):
    return event_service.publish_event(db=db, event=event, actor_id=user.id)


@router.post("/unpublish", response_model=EventResponse)
def unpublish_event(
    event: Event = Depends(owned_event_guard),
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.unpublish_event(db=db, event=event, actor_id=user.id)


@router.post("/cancel", response_model=EventResponse)
def cancel_event(
    event: Event = Depends(owned_event_guard),
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.cancel_event(db=db, event=event, actor_id=user.id)


@router.get("/access-link", response_model=EventAccessLinkResponse)
def get_event_access_link(event: Event = Depends(owned_event_id_guard)):
    return EventAccessLinkResponse(
        link=f"{settings.FRONTEND_URL}/events/detail?event_id={event.id}&access={event.access_token}"
    )


@router.post("/duplicate", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def duplicate_event(
    event: Event = Depends(owned_event_id_guard),
    user: User = Depends(require_role("organizer")),
    db: Session = Depends(get_db),
):
    return event_service.duplicate_event(db=db, event=event, actor_id=user.id)
