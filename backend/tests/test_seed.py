from sqlalchemy import func, select

import core
from core import *
from features.events.models import Event
from features.ticket_types.models import TicketType
from features.users.models import User
from scripts.seed import seed


def test_seed_is_idempotent(client) -> None:
    with Session(core.engine) as db:
        seed(db)
        seed(db)

        roles = list(db.scalars(select(User.role)).all())
        assert sorted(roles) == ["attendee", "event_admin", "organizer", "platform_admin"]
        assert db.scalar(select(func.count()).select_from(Event)) == 1
        assert db.scalar(select(func.count()).select_from(TicketType)) == 1
