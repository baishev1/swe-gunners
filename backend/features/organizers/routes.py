from fastapi import APIRouter, Depends

from core import *

from .guards import *
from .models import *
from .schemas import *
from .service import organizer_service

router = APIRouter(prefix="/organizers", tags=["Organizers"])


@router.get("/profile", response_model=OrganizerProfileResponse)
def get_profile(profile: OrganizerProfile = Depends(organizer_profile_guard)):
    return profile


@router.patch("/profile", response_model=OrganizerProfileResponse)
def update_profile(
    data: OrganizerProfileUpdate,
    profile: OrganizerProfile = Depends(organizer_profile_guard),
    db: Session = Depends(get_db),
):
    return organizer_service.update_profile(db=db, profile=profile, data=data)
