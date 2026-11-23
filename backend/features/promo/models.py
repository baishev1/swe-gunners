from urllib.parse import urlencode

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.events.models import Event
from features.ticket_types.models import TicketType


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

    event: Mapped[Event] = relationship()
    # Empty means the discount applies to every ticket type of the event.
    ticket_types: Mapped[list[TicketType]] = relationship(
        secondary="promo_campaign_ticket_type", lazy="selectin"
    )

    @property
    def ticket_type_ids(self) -> list[UUID]:
        return [ticket_type.id for ticket_type in self.ticket_types]

    @property
    def link(self) -> str:
        query = urlencode({"event_id": self.event_id, "promo": self.qr_token})
        return f"{settings.FRONTEND_URL}/events/detail?{query}"


class PromoCampaignTicketType(DbBase):
    campaign_id: Mapped[UUID] = mapped_column(ForeignKey("promo_campaign.id"))
    ticket_type_id: Mapped[UUID] = mapped_column(ForeignKey("ticket_type.id"))


class PromoRedemption(DbBase):
    campaign_id: Mapped[UUID] = mapped_column(ForeignKey("promo_campaign.id"))
    # TODO: point at order.id once features/orders is merged
    order_id: Mapped[UUID]
    discount_amount: Mapped[int] = mapped_column(Integer)
