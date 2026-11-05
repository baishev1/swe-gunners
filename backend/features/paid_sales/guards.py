from fastapi import Depends, HTTPException, status

from core import *
from features.events.guards import owned_event_guard
from features.events.models import Event

from .models import *
from .service import paid_sales_service


def pending_activation_event_guard(
    event: Event = Depends(owned_event_guard),
    db: Session = Depends(get_db),
) -> Event:
    activation = paid_sales_service.get_activation(db, event.id)
    if activation and activation.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paid sales for this event were suspended by a platform admin",
        )
    if activation and activation.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid sales are already active for this event",
        )
    return event


def activatable_event_guard(
    event: Event = Depends(pending_activation_event_guard),
    db: Session = Depends(get_db),
) -> Event:
    checklist = paid_sales_service.build_checklist(db, event)
    missing = [
        label
        for done, label in (
            (checklist.has_paid_ticket_type, "a paid ticket type"),
            (checklist.identity_verified, "identity verification"),
            (checklist.payout_account_ready, "a payout account"),
            (checklist.fee_paid, "the activation fee"),
            (checklist.terms_accepted, "accepted paid-event terms"),
        )
        if not done
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Paid sales activation is missing: {', '.join(missing)}",
        )
    return event


def valid_activation_for_event(
    event_id: UUID, db: Session = Depends(get_db)
) -> PaidSalesActivation:
    activation = paid_sales_service.get_activation(db, event_id)
    if not activation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paid sales activation not found",
        )
    return activation


def suspendable_activation_guard(
    activation: PaidSalesActivation = Depends(valid_activation_for_event),
) -> PaidSalesActivation:
    if activation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Paid sales are not active (status '{activation.status}')",
        )
    return activation


def reinstatable_activation_guard(
    activation: PaidSalesActivation = Depends(valid_activation_for_event),
) -> PaidSalesActivation:
    if activation.status != "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Paid sales are not suspended",
        )
    return activation
