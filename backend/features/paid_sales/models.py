from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import *
from features.events.models import Event


class PaidSalesActivation(DbBase):
    """Per-event record of the Paid Sales Activation checklist (SRS 3.2, 4.5)."""

    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    fee_amount: Mapped[int | None] = mapped_column(Integer, default=None)
    fee_transaction_id: Mapped[str | None] = mapped_column(String(100), default=None)
    fee_paid_at: Mapped[AwareDateTime | None] = mapped_column(default=None)
    terms_accepted_at: Mapped[AwareDateTime | None] = mapped_column(default=None)
    activated_at: Mapped[AwareDateTime | None] = mapped_column(default=None)
    suspended_at: Mapped[AwareDateTime | None] = mapped_column(default=None)
    suspension_reason: Mapped[str | None] = mapped_column(String(500), default=None)

    event: Mapped[Event] = relationship(lazy="joined")

    @property
    def event_title(self) -> str:
        return self.event.title
