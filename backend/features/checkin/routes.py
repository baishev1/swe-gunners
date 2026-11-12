from fastapi import APIRouter, Depends, Query, status

from core import *
from features.events.models import Event
from features.events.schemas import EventResponse
from features.users.dependencies import active_user
from features.users.models import User

from .guards import *
from .models import *
from .schemas import *
from .service import checkin_service

router = APIRouter(prefix="/checkin", tags=["Check-in"])


@router.get("/events", response_model=list[EventResponse])
def list_assigned_events(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(active_user),
    db: Session = Depends(get_db),
):
    return checkin_service.list_events(db, user, limit, offset)


@router.post("/staff", response_model=StaffAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_staff(
    data: StaffAssignmentCreate = Depends(valid_staff_assignment),
    event: Event = Depends(managed_event),
    db: Session = Depends(get_db),
):
    return checkin_service.assign_staff(db, event, data)


@router.get("/staff", response_model=list[StaffAssignmentResponse])
def list_staff(
    event: Event = Depends(managed_event),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return checkin_service.list_staff(db, event, limit, offset)


@router.delete("/staff", status_code=status.HTTP_204_NO_CONTENT)
def revoke_staff(
    assignment: StaffAssignment = Depends(managed_assignment),
    db: Session = Depends(get_db),
):
    checkin_service.revoke_staff(db, assignment)
