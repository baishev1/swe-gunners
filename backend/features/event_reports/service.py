from sqlalchemy import select

from core import *
from features.audit_log.service import audit_log_service
from features.events.models import Event

from .models import *
from .schemas import *


class EventReportService:
    def create(
        self, db: Session, event: Event, data: EventReportCreate, reporter_id: UUID
    ) -> EventReport:
        report = EventReport(**data.model_dump(), event_id=event.id, reporter_id=reporter_id)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def list_reports(self, db: Session, status: str | None = None) -> list[EventReport]:
        stmt = select(EventReport)
        if status:
            stmt = stmt.where(EventReport.status == status)
        stmt = stmt.order_by(EventReport.created_at.desc())
        return list(db.scalars(stmt).all())

    def review(self, db: Session, report: EventReport, actor_id: UUID) -> EventReport:
        report.status = "reviewed"
        audit_log_service.record(
            db,
            action="event_report_reviewed",
            entity_type="event_report",
            entity_id=report.id,
            description=f"Reviewed a {report.category} report on {report.event.title}",
            event_id=report.event_id,
            actor_id=actor_id,
        )
        db.commit()
        db.refresh(report)
        return report


event_report_service = EventReportService()
