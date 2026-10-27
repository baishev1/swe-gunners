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


audit_log_service = AuditLogService()
