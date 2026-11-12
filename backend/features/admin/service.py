import csv
from datetime import datetime
from io import StringIO
from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event
from features.orders.models import Order
from features.payments.models import Payment
from features.promo.models import PromoCampaign
from features.users.models import User

from .models import *
from .schemas import *


class AdminService:
    def search_users(
        self, db: Session, q: str | None = None, role: str | None = None
    ) -> list[User]:
        stmt = select(User)
        if q:
            stmt = stmt.where(or_(User.email.ilike(f"%{q}%"), User.full_name.ilike(f"%{q}%")))
        if role:
            stmt = stmt.where(User.role == role)
        return list(db.scalars(stmt.order_by(User.created_at.desc())).all())

    def suspend_user(self, db: Session, user: User, actor_id: UUID) -> User:
        user.is_active = False
        audit_log_service.record(
            db,
            action="user_suspended",
            entity_type="user",
            entity_id=user.id,
            description=f"Suspended user {user.email}",
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(user)
        return user

    def search_events(
        self, db: Session, q: str | None = None, status: str | None = None
    ) -> list[Event]:
        stmt = select(Event)
        if q:
            stmt = stmt.where(Event.title.ilike(f"%{q}%"))
        if status:
            stmt = stmt.where(Event.status == status)
        return list(db.scalars(stmt.order_by(Event.start_time.desc())).all())

    def suspend_event(self, db: Session, event: Event, actor_id: UUID) -> Event:
        event.status = "suspended"
        audit_log_service.record(
            db,
            action="event_suspended",
            entity_type="event",
            entity_id=event.id,
            description=f"Suspended event {event.title}",
            event_id=event.id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(event)
        return event

    def search_campaigns(self, db: Session, q: str | None = None) -> list[PromoCampaign]:
        stmt = select(PromoCampaign)
        if q:
            stmt = stmt.where(
                or_(
                    PromoCampaign.code.ilike(f"%{q}%"),
                    PromoCampaign.name.ilike(f"%{q}%"),
                )
            )
        return list(db.scalars(stmt.order_by(PromoCampaign.created_at.desc())).all())

    def get_settings(self, db: Session) -> PlatformSetting:
        setting = db.scalars(select(PlatformSetting)).first()
        if setting is None:
            setting = PlatformSetting()
            db.add(setting)
            db.commit()
            db.refresh(setting)
        return setting

    def update_settings(
        self, db: Session, data: PlatformSettingUpdate, actor_id: UUID
    ) -> PlatformSetting:
        setting = self.get_settings(db)
        setting.activation_fee = data.activation_fee
        audit_log_service.record(
            db,
            action="settings_updated",
            entity_type="platform_setting",
            entity_id=setting.id,
            description=f"Set activation fee to {data.activation_fee} tiyn",
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(setting)
        return setting

    def search_orders(
        self, db: Session, q: str | None = None, status: str | None = None, limit: int = 100
    ) -> list[AdminOrderResponse]:
        stmt = select(Order, Event.title).outerjoin(Event, Event.id == Order.event_id)
        if q:
            stmt = stmt.where(
                self._match(
                    q,
                    ids=[Order.id, Order.event_id, Order.user_id],
                    texts=[Order.customer_email, Order.customer_name, Event.title],
                )
            )
        if status:
            stmt = stmt.where(Order.status == status)
        rows = db.execute(stmt.order_by(Order.created_at.desc()).limit(limit)).all()
        return [self._order_response(order, title) for order, title in rows]

    def search_payments(
        self, db: Session, q: str | None = None, status: str | None = None, limit: int = 100
    ) -> list[AdminPaymentResponse]:
        stmt = self._payment_query()
        if q:
            stmt = stmt.where(
                self._match(
                    q,
                    ids=[Payment.id, Payment.order_id],
                    texts=[Payment.transaction_id, Order.customer_email, Event.title],
                )
            )
        if status:
            stmt = stmt.where(Payment.status == status)
        rows = db.execute(stmt.order_by(Payment.created_at.desc()).limit(limit)).all()
        return [self._payment_response(*row) for row in rows]

    def monitoring(self, db: Session, recent: int = 10) -> AdminMonitoringResponse:
        def count_orders(status: str) -> int:
            return db.scalar(select(func.count(Order.id)).where(Order.status == status)) or 0

        failed_rows = db.execute(
            self._payment_query()
            .where(Payment.status == "failed")
            .order_by(Payment.created_at.desc())
            .limit(recent)
        ).all()
        refund_rows = db.execute(
            select(Order, Event.title)
            .outerjoin(Event, Event.id == Order.event_id)
            .where(Order.status == "refunded")
            .order_by(Order.updated_at.desc())
            .limit(recent)
        ).all()
        return AdminMonitoringResponse(
            failed_payments=db.scalar(
                select(func.count(Payment.id)).where(Payment.status == "failed")
            )
            or 0,
            refunded_orders=count_orders("refunded"),
            refunded_amount_kzt=db.scalar(
                select(func.coalesce(func.sum(Order.total_amount_kzt), 0)).where(
                    Order.status == "refunded"
                )
            )
            or 0,
            cancelled_orders=count_orders("cancelled"),
            pending_orders=count_orders("pending"),
            recent_failed_payments=[self._payment_response(*row) for row in failed_rows],
            recent_refunds=[self._order_response(order, title) for order, title in refund_rows],
        )

    def export_report(
        self,
        db: Session,
        report: ReportKind,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> str:
        """Builds a CSV of one record type, optionally limited to a creation date range."""
        header: list[str]
        rows: list[list[object]]
        match report:
            case "orders":
                header = [
                    "id",
                    "created_at",
                    "event_id",
                    "event_title",
                    "customer_name",
                    "customer_email",
                    "total_amount_kzt",
                    "status",
                ]
                order_stmt = self._in_range(
                    select(Order, Event.title).outerjoin(Event, Event.id == Order.event_id),
                    Order.created_at,
                    date_from,
                    date_to,
                )
                rows = [
                    [
                        o.id,
                        o.created_at.isoformat(),
                        o.event_id,
                        title,
                        o.customer_name,
                        o.customer_email,
                        o.total_amount_kzt,
                        o.status,
                    ]
                    for o, title in db.execute(order_stmt.order_by(Order.created_at)).all()
                ]
            case "payments":
                header = [
                    "id",
                    "created_at",
                    "order_id",
                    "transaction_id",
                    "provider",
                    "amount_kzt",
                    "status",
                    "customer_email",
                    "event_title",
                ]
                payment_stmt = self._in_range(
                    self._payment_query(), Payment.created_at, date_from, date_to
                )
                rows = [
                    [
                        p.id,
                        p.created_at.isoformat(),
                        p.order_id,
                        p.transaction_id,
                        p.provider,
                        p.amount_kzt,
                        p.status,
                        email,
                        title,
                    ]
                    for p, email, title in db.execute(
                        payment_stmt.order_by(Payment.created_at)
                    ).all()
                ]
            case "events":
                header = [
                    "id",
                    "created_at",
                    "title",
                    "status",
                    "organizer_id",
                    "start_time",
                    "end_time",
                    "capacity",
                ]
                event_stmt = self._in_range(select(Event), Event.created_at, date_from, date_to)
                rows = [
                    [
                        e.id,
                        e.created_at.isoformat(),
                        e.title,
                        e.status,
                        e.organizer_id,
                        e.start_time.isoformat(),
                        e.end_time.isoformat(),
                        e.capacity,
                    ]
                    for e in db.scalars(event_stmt.order_by(Event.created_at)).all()
                ]
            case "users":
                header = [
                    "id",
                    "created_at",
                    "email",
                    "full_name",
                    "role",
                    "is_active",
                    "is_email_verified",
                ]
                user_stmt = self._in_range(select(User), User.created_at, date_from, date_to)
                rows = [
                    [
                        u.id,
                        u.created_at.isoformat(),
                        u.email,
                        u.full_name,
                        u.role,
                        u.is_active,
                        u.is_email_verified,
                    ]
                    for u in db.scalars(user_stmt.order_by(User.created_at)).all()
                ]

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(header)
        writer.writerows([[self._csv_cell(value) for value in row] for row in rows])
        return buffer.getvalue()

    def _payment_query(self) -> Select[tuple[Payment, str, str]]:
        return (
            select(Payment, Order.customer_email, Event.title)
            .outerjoin(Order, Order.id == Payment.order_id)
            .outerjoin(Event, Event.id == Order.event_id)
        )

    def _match(
        self,
        q: str,
        ids: list[InstrumentedAttribute[Any]],
        texts: list[InstrumentedAttribute[str]],
    ) -> ColumnElement[bool]:
        """A full UUID matches the id columns exactly; anything else is a text search."""
        q = q.strip()
        try:
            exact = UUID(q)
        except ValueError:
            return or_(*(column.ilike(f"%{q}%") for column in texts))
        return or_(*(column == exact for column in ids))

    def _in_range[T: tuple[object, ...]](
        self,
        stmt: Select[T],
        column: InstrumentedAttribute[datetime],
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> Select[T]:
        if date_from:
            stmt = stmt.where(column >= date_from)
        if date_to:
            stmt = stmt.where(column < date_to)
        return stmt

    def _csv_cell(self, value: object) -> object:
        # Spreadsheet apps run cells starting with these characters as formulas.
        if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
            return f"'{value}"
        return value

    def _order_response(self, order: Order, event_title: str | None) -> AdminOrderResponse:
        return AdminOrderResponse(
            id=order.id,
            event_id=order.event_id,
            event_title=event_title,
            user_id=order.user_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            total_amount_kzt=order.total_amount_kzt,
            status=order.status,
            created_at=order.created_at,
        )

    def _payment_response(
        self, payment: Payment, customer_email: str | None, event_title: str | None
    ) -> AdminPaymentResponse:
        return AdminPaymentResponse(
            id=payment.id,
            order_id=payment.order_id,
            amount_kzt=payment.amount_kzt,
            status=payment.status,
            provider=payment.provider,
            transaction_id=payment.transaction_id,
            customer_email=customer_email,
            event_title=event_title,
            created_at=payment.created_at,
        )


admin_service = AdminService()
