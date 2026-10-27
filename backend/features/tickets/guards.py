from fastapi import Depends, HTTPException, status

from core import *

from .models import *
from .schemas import *


def valid_ticket_id(ticket_id: UUID, db: Session = Depends(get_db)) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket
