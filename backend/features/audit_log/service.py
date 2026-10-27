from datetime import datetime

from sqlalchemy import select

from core import *

from .models import *


class AuditLogService:
    def record(
        self,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: UUID,
        description: str,
        event_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> AuditLog:
        """Adds the entry without committing, so it lands in the caller's transaction."""
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            event_id=event_id,
            actor_id=actor_id,
        )
        db.add(entry)
        return entry

    def list_event_entries(
        self,
        db: Session,
        event_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        action: str | None = None,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.event_id == event_id)
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLog.created_at < date_to)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        return list(db.scalars(stmt.order_by(AuditLog.created_at)).all())


audit_log_service = AuditLogService()
