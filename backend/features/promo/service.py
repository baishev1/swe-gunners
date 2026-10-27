import secrets

from sqlalchemy import select

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event

from .models import *
from .schemas import *

# No 0/O or 1/I, so a code read off a poster is typed correctly.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8


class PromoService:
    def create_campaign(
        self, db: Session, event: Event, data: PromoCampaignCreate
    ) -> PromoCampaign:
        campaign = PromoCampaign(
            **data.model_dump(),
            event_id=event.id,
            code="".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH)),
            qr_token=secrets.token_urlsafe(32),
        )
        db.add(campaign)
        db.flush()
        audit_log_service.record(
            db,
            action="promo_created",
            entity_type="promo_campaign",
            entity_id=campaign.id,
            description=f"Created promo campaign {campaign.name} ({campaign.code})",
            event_id=event.id,
        )
        db.commit()
        db.refresh(campaign)
        return campaign

    def list_campaigns(self, db: Session, event_id: UUID) -> list[PromoCampaign]:
        stmt = (
            select(PromoCampaign)
            .where(PromoCampaign.event_id == event_id)
            .order_by(PromoCampaign.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def update_campaign(
        self, db: Session, campaign: PromoCampaign, data: PromoCampaignUpdate
    ) -> PromoCampaign:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(campaign, key, value)
        db.commit()
        db.refresh(campaign)
        return campaign

    def disable_campaign(self, db: Session, campaign: PromoCampaign) -> PromoCampaign:
        campaign.is_disabled = True
        audit_log_service.record(
            db,
            action="promo_disabled",
            entity_type="promo_campaign",
            entity_id=campaign.id,
            description=f"Disabled promo campaign {campaign.name} ({campaign.code})",
            event_id=campaign.event_id,
        )
        db.commit()
        db.refresh(campaign)
        return campaign


promo_service = PromoService()
