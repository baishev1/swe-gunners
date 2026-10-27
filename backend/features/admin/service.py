from sqlalchemy import or_, select

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event
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


admin_service = AdminService()
