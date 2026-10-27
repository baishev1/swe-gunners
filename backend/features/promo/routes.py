from fastapi import APIRouter, Depends, Response, status

from core import *
from features.events.models import Event

from .guards import *
from .models import *
from .schemas import *
from .service import promo_service

router = APIRouter(prefix="/promo", tags=["Promo"])


@router.post(
    "/campaigns", response_model=PromoCampaignResponse, status_code=status.HTTP_201_CREATED
)
def create_campaign(
    data: PromoCampaignCreate,
    event: Event = Depends(editable_event_guard),
    db: Session = Depends(get_db),
):
    return promo_service.create_campaign(db=db, event=event, data=data)


@router.get("/campaigns", response_model=list[PromoCampaignResponse])
def list_campaigns(event: Event = Depends(valid_event_id), db: Session = Depends(get_db)):
    return promo_service.list_campaigns(db=db, event_id=event.id)


@router.get("/campaigns/detail", response_model=PromoCampaignResponse)
def get_campaign_detail(campaign: PromoCampaign = Depends(valid_campaign_id)):
    return campaign


@router.patch("/campaigns/update", response_model=PromoCampaignResponse)
def update_campaign(
    data: PromoCampaignUpdate = Depends(valid_campaign_update),
    campaign: PromoCampaign = Depends(enabled_campaign_guard),
    db: Session = Depends(get_db),
):
    return promo_service.update_campaign(db=db, campaign=campaign, data=data)


@router.post("/campaigns/disable", response_model=PromoCampaignResponse)
def disable_campaign(
    campaign: PromoCampaign = Depends(enabled_campaign_guard),
    db: Session = Depends(get_db),
):
    return promo_service.disable_campaign(db=db, campaign=campaign)


@router.get("/campaigns/qr", response_class=Response)
def get_campaign_qr(campaign: PromoCampaign = Depends(valid_campaign_id)):
    return Response(content=promo_service.build_qr_svg(campaign), media_type="image/svg+xml")


@router.get("/resolve", response_model=PromoCampaignPublicResponse)
def resolve_promo_link(campaign: PromoCampaign = Depends(redeemable_campaign_guard)):
    return campaign
