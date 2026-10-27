from fastapi import Depends, HTTPException, status

from core import *
from features.events.models import Event

from .models import *
from .schemas import *
from .service import promo_service


def valid_event_id(event_id: UUID, db: Session = Depends(get_db)) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def editable_event_guard(event: Event = Depends(valid_event_id)) -> Event:
    if event.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify a cancelled event",
        )
    return event


def valid_campaign_id(campaign_id: UUID, db: Session = Depends(get_db)) -> PromoCampaign:
    campaign = db.get(PromoCampaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


def enabled_campaign_guard(
    campaign: PromoCampaign = Depends(valid_campaign_id),
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
