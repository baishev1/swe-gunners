from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from core import *
from features.auth.guards import require_role
from features.events.guards import owned_event_guard
from features.events.models import Event
from features.ticket_types.models import TicketType
from features.users.models import User

from .models import *
from .schemas import *
from .service import promo_service


def valid_campaign_create(
    data: PromoCampaignCreate,
    event: Event = Depends(owned_event_guard),
    db: Session = Depends(get_db),
) -> PromoCampaignCreate:
    requested = set(data.ticket_type_ids)
    if requested:
        found = db.scalars(
            select(TicketType.id).where(
                TicketType.id.in_(requested), TicketType.event_id == event.id
            )
        ).all()
        if set(found) != requested:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket type does not belong to this event",
            )
    return data


def valid_campaign_id(campaign_id: UUID, db: Session = Depends(get_db)) -> PromoCampaign:
    campaign = db.get(PromoCampaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


def owned_campaign_guard(
    campaign: PromoCampaign = Depends(valid_campaign_id),
    user: User = Depends(require_role("organizer")),
) -> PromoCampaign:
    if campaign.event.organizer_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


def enabled_campaign_guard(
    campaign: PromoCampaign = Depends(owned_campaign_guard),
) -> PromoCampaign:
    if campaign.is_disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is disabled",
        )
    return campaign


def valid_qr_token(token: str, db: Session = Depends(get_db)) -> PromoCampaign:
    campaign = promo_service.find_by_qr_token(db, token)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo link is not valid",
        )
    return campaign


def redeemable_campaign_guard(
    campaign: PromoCampaign = Depends(valid_qr_token),
) -> PromoCampaign:
    error = promo_service.redeem_error(campaign)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return campaign


def valid_campaign_update(
    data: PromoCampaignUpdate,
    campaign: PromoCampaign = Depends(enabled_campaign_guard),
) -> PromoCampaignUpdate:
    start_time = data.start_time or campaign.start_time
    end_time = data.end_time or campaign.end_time
    if start_time and end_time and end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time",
        )
    if data.max_redemptions is not None and data.max_redemptions < campaign.redemption_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_redemptions is below the number of redemptions already made",
        )
    return data
