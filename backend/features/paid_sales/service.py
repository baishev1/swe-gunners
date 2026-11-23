from uuid import uuid4

from sqlalchemy import select

from core import *
from features.admin.service import admin_service
from features.audit_log.service import audit_log_service
from features.events.models import Event
from features.notifications.service import notification_service
from features.organizers.models import OrganizerProfile
from features.ticket_types.models import TicketType
from features.users.models import User

from .models import *
from .schemas import *

CLOSED_EVENT_STATUSES = ("cancelled", "suspended")


class PaidSalesService:
    def get_activation(self, db: Session, event_id: UUID) -> PaidSalesActivation | None:
        return db.scalar(
            select(PaidSalesActivation).where(PaidSalesActivation.event_id == event_id)
        )

    def get_or_create_activation(self, db: Session, event: Event) -> PaidSalesActivation:
        activation = self.get_activation(db, event.id)
        if activation is None:
            activation = PaidSalesActivation(event_id=event.id)
            db.add(activation)
            db.flush()
        return activation

    def is_open(self, db: Session, event_id: UUID) -> bool:
        """Paid tickets can be bought only while the event is activated and not closed."""
        activation = self.get_activation(db, event_id)
        return (
            activation is not None
            and activation.status == "active"
            and activation.event.status not in CLOSED_EVENT_STATUSES
        )

    def build_checklist(self, db: Session, event: Event) -> PaidSalesChecklistResponse:
        activation = self.get_activation(db, event.id)
        profile = db.scalar(
            select(OrganizerProfile).where(OrganizerProfile.user_id == event.organizer_id)
        )
        has_paid_ticket_type = (
            db.scalar(
                select(TicketType.id)
                .where(TicketType.event_id == event.id, TicketType.price > 0)
                .limit(1)
            )
            is not None
        )
        identity_verified = bool(profile and profile.identity_verified_at)
        payout_account_ready = bool(profile and profile.has_payout_account)
        fee_paid = bool(activation and activation.fee_paid_at)
        terms_accepted = bool(activation and activation.terms_accepted_at)
        status = activation.status if activation else "pending"
        fee_amount = (
            activation.fee_amount
            if activation and activation.fee_amount is not None
            else admin_service.get_settings(db).activation_fee
        )
        return PaidSalesChecklistResponse(
            event_id=event.id,
            status=status,
            fee_amount=fee_amount,
            fee_transaction_id=activation.fee_transaction_id if activation else None,
            fee_paid_at=activation.fee_paid_at if activation else None,
            terms_accepted_at=activation.terms_accepted_at if activation else None,
            activated_at=activation.activated_at if activation else None,
            suspended_at=activation.suspended_at if activation else None,
            suspension_reason=activation.suspension_reason if activation else None,
            has_paid_ticket_type=has_paid_ticket_type,
            identity_verified=identity_verified,
            payout_account_ready=payout_account_ready,
            fee_paid=fee_paid,
            terms_accepted=terms_accepted,
            can_activate=status == "pending"
            and has_paid_ticket_type
            and identity_verified
            and payout_account_ready
            and fee_paid
            and terms_accepted,
        )

    def pay_fee(self, db: Session, event: Event, actor_id: UUID, simulate_failure: bool) -> None:
        """Records a simulated activation-fee payment; no real money moves."""
        fee = admin_service.get_settings(db).activation_fee
        if simulate_failure:
            audit_log_service.record(
                db,
                action="activation_fee_failed",
                entity_type="event",
                entity_id=event.id,
                description="Simulated activation fee payment failed",
                event_id=event.id,
                actor_id=actor_id,
            )
            db.commit()
            return
        activation = self.get_or_create_activation(db, event)
        activation.fee_amount = fee
        activation.fee_transaction_id = f"sim_{uuid4().hex[:16]}"
        activation.fee_paid_at = time_now()
        audit_log_service.record(
            db,
            action="activation_fee_paid",
            entity_type="paid_sales_activation",
            entity_id=activation.id,
            description=f"Paid simulated activation fee of {fee} tiyn",
            event_id=event.id,
            actor_id=actor_id,
        )
        db.commit()

    def accept_terms(self, db: Session, event: Event, actor_id: UUID) -> None:
        activation = self.get_or_create_activation(db, event)
        if activation.terms_accepted_at is None:
            activation.terms_accepted_at = time_now()
            audit_log_service.record(
                db,
                action="paid_terms_accepted",
                entity_type="paid_sales_activation",
                entity_id=activation.id,
                description="Accepted the paid-event terms",
                event_id=event.id,
                actor_id=actor_id,
            )
        db.commit()

    def activate(self, db: Session, event: Event, actor_id: UUID) -> None:
        activation = self.get_or_create_activation(db, event)
        activation.status = "active"
        activation.activated_at = time_now()
        audit_log_service.record(
            db,
            action="paid_sales_activated",
            entity_type="paid_sales_activation",
            entity_id=activation.id,
            description="Activated paid ticket sales",
            event_id=event.id,
            actor_id=actor_id,
        )
        db.commit()
        self._notify_payout_status(db, event, "active")

    def list_activations(self, db: Session, status: str | None = None) -> list[PaidSalesActivation]:
        stmt = select(PaidSalesActivation)
        if status:
            stmt = stmt.where(PaidSalesActivation.status == status)
        return list(db.scalars(stmt.order_by(PaidSalesActivation.updated_at.desc())).all())

    def suspend(
        self, db: Session, activation: PaidSalesActivation, reason: str, actor_id: UUID
    ) -> PaidSalesActivation:
        activation.status = "suspended"
        activation.suspended_at = time_now()
        activation.suspension_reason = reason
        audit_log_service.record(
            db,
            action="paid_sales_suspended",
            entity_type="paid_sales_activation",
            entity_id=activation.id,
            description=f"Suspended paid sales: {reason}"[:500],
            event_id=activation.event_id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(activation)
        self._notify_payout_status(db, activation.event, "suspended", reason)
        return activation

    def reinstate(
        self, db: Session, activation: PaidSalesActivation, actor_id: UUID
    ) -> PaidSalesActivation:
        activation.status = "active"
        activation.suspended_at = None
        activation.suspension_reason = None
        audit_log_service.record(
            db,
            action="paid_sales_reinstated",
            entity_type="paid_sales_activation",
            entity_id=activation.id,
            description="Reinstated paid sales",
            event_id=activation.event_id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(activation)
        self._notify_payout_status(db, activation.event, "reinstated")
        return activation

    def _notify_payout_status(
        self, db: Session, event: Event, status: str, reason: str | None = None
    ) -> None:
        organizer = db.get(User, event.organizer_id)
        if organizer is not None:
            notification_service.payout_status_changed(organizer.email, event.title, status, reason)


paid_sales_service = PaidSalesService()
