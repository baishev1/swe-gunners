from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime

from core import *
from features.auth.guards import require_role

from .schemas import *
from .service import operations_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("platform_admin"))],
)


@router.get("/orders", response_model=list[AdminOrderResponse])
def search_orders(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    return operations_service.search_orders(db=db, q=q, status=status)


@router.get("/payments", response_model=list[AdminPaymentResponse])
def search_payments(q: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    return operations_service.search_payments(db=db, q=q, status=status)


@router.get("/monitoring", response_model=AdminMonitoringResponse)
def get_monitoring(db: Session = Depends(get_db)):
    return operations_service.monitoring(db=db)


@router.get("/reports/export", response_class=Response)
def export_report(
    report: ReportKind = Query(),
    date_from: AwareDatetime | None = None,
    date_to: AwareDatetime | None = None,
    db: Session = Depends(get_db),
):
    content = operations_service.export_report(
        db=db, report=report, date_from=date_from, date_to=date_to
    )
    filename = f"biletflow-{report}-{time_now():%Y%m%d}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
