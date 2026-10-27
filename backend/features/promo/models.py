from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core import *


class PromoCampaign(DbBase):
    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"))
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(20), unique=True)
    qr_token: Mapped[str] = mapped_column(String(64), unique=True)
    discount_type: Mapped[str] = mapped_column(String(20))
    # Percent for "percent", tiyn for "fixed".
    discount_value: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    end_time: Mapped[AwareDateTime | None] = mapped_column(default=None)
    max_redemptions: Mapped[int | None] = mapped_column(Integer, default=None)
    redemption_count: Mapped[int] = mapped_column(Integer, default=0)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # TODO: add applicable ticket types once features/ticket_types is merged


class PromoRedemption(DbBase):
    campaign_id: Mapped[UUID] = mapped_column(ForeignKey("promo_campaign.id"))
    # TODO: point at order.id once features/orders is merged
    order_id: Mapped[UUID]
    discount_amount: Mapped[int] = mapped_column(Integer)
