from fastapi import Depends, HTTPException, status

from core import *

from .models import *


def valid_report_id(report_id: UUID, db: Session = Depends(get_db)) -> EventReport:
    report = db.get(EventReport, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


def open_report_guard(report: EventReport = Depends(valid_report_id)) -> EventReport:
    if report.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is already reviewed",
        )
    return report
