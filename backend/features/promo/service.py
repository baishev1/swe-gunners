import secrets

import qrcode
from qrcode.constants import ERROR_CORRECT_M
from sqlalchemy import or_, select, update

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event
from features.ticket_types.models import TicketType

from .models import *
from .schemas import *

# No 0/O or 1/I, so a code read off a poster is typed correctly.
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8

# Spec 4.14: a campaign QR must not look like an admission ticket QR.
QR_COLOR = "#6D28D9"
QR_CAPTION = "PROMO - NOT A TICKET"
QR_MODULE_SIZE = 10


class PromoService:
    def create_campaign(
        self, db: Session, event: Event, data: PromoCampaignCreate, actor_id: UUID
    ) -> PromoCampaign:
        ticket_types = db.scalars(
            select(TicketType).where(TicketType.id.in_(set(data.ticket_type_ids)))
        ).all()
        campaign = PromoCampaign(
            **data.model_dump(exclude={"ticket_type_ids"}),
            ticket_types=list(ticket_types),
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
            actor_id=actor_id,
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

    def disable_campaign(
        self, db: Session, campaign: PromoCampaign, actor_id: UUID
    ) -> PromoCampaign:
        campaign.is_disabled = True
        audit_log_service.record(
            db,
            action="promo_disabled",
            entity_type="promo_campaign",
            entity_id=campaign.id,
            description=f"Disabled promo campaign {campaign.name} ({campaign.code})",
            event_id=campaign.event_id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(campaign)
        return campaign

    def campaign_link(self, campaign: PromoCampaign) -> str:
        return campaign.link

    def build_qr_svg(self, campaign: PromoCampaign) -> str:
        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=4)
        qr.add_data(self.campaign_link(campaign))
        qr.make(fit=True)
        matrix = qr.get_matrix()

        m = QR_MODULE_SIZE
        size = len(matrix) * m
        path = "".join(
            f"M{x * m},{y * m}h{m}v{m}h-{m}z"
            for y, row in enumerate(matrix)
            for x, is_dark in enumerate(row)
            if is_dark
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size + 60}">'
            f'<rect width="100%" height="100%" fill="#ffffff"/>'
            f'<path d="{path}" fill="{QR_COLOR}"/>'
            f'<text x="{size // 2}" y="{size + 36}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="24" font-weight="bold" fill="{QR_COLOR}">'
            f"{QR_CAPTION}</text></svg>"
        )

    def find_by_qr_token(self, db: Session, token: str) -> PromoCampaign | None:
        return db.scalars(select(PromoCampaign).where(PromoCampaign.qr_token == token)).first()

    def find_by_code(self, db: Session, event_id: UUID, code: str) -> PromoCampaign | None:
        stmt = select(PromoCampaign).where(
            PromoCampaign.event_id == event_id,
            PromoCampaign.code == code.strip().upper(),
        )
        return db.scalars(stmt).first()

    def redeem_error(self, campaign: PromoCampaign) -> str | None:
        now = time_now()
        if campaign.is_disabled:
            return "Promo code is disabled"
        if campaign.start_time and now < campaign.start_time:
            return "Promo code is not active yet"
        if campaign.end_time and now >= campaign.end_time:
            return "Promo code has expired"
        if (
            campaign.max_redemptions is not None
            and campaign.redemption_count >= campaign.max_redemptions
        ):
            return "Promo code has reached its redemption limit"
        return None

    def applies_to(self, campaign: PromoCampaign, ticket_type_id: UUID) -> bool:
        return not campaign.ticket_types or ticket_type_id in campaign.ticket_type_ids

    def calculate_discount(self, campaign: PromoCampaign, subtotal: int) -> int:
        """`subtotal` covers only the order items that `applies_to` accepts."""
        if campaign.discount_type == "percent":
            return subtotal * campaign.discount_value // 100
        return min(campaign.discount_value, subtotal)

    def redeem(
        self, db: Session, campaign: PromoCampaign, order_id: UUID, discount_amount: int
    ) -> PromoRedemption | None:
        """
        Called from payment confirmation. Does not commit. Returns None when the campaign
        stopped being redeemable since checkout started, so the caller can fail the order.
        """
        if self.redeem_error(campaign):
            return None

        # The limit is checked inside the UPDATE so two confirmations cannot both take
        # the last redemption.
        stmt = (
            update(PromoCampaign)
            .where(
                PromoCampaign.id == campaign.id,
                PromoCampaign.is_disabled.is_(False),
                or_(
                    PromoCampaign.max_redemptions.is_(None),
                    PromoCampaign.redemption_count < PromoCampaign.max_redemptions,
                ),
            )
            .values(redemption_count=PromoCampaign.redemption_count + 1)
            .returning(PromoCampaign.id)
        )
        if db.scalars(stmt).first() is None:
            return None

        redemption = PromoRedemption(
            campaign_id=campaign.id, order_id=order_id, discount_amount=discount_amount
        )
        db.add(redemption)
        return redemption


promo_service = PromoService()
