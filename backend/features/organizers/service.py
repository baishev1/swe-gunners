from core import *

from .models import *
from .schemas import *


class OrganizerService:
    def update_profile(
        self, db: Session, profile: OrganizerProfile, data: OrganizerProfileUpdate
    ) -> OrganizerProfile:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile


organizer_service = OrganizerService()
