from fastapi import APIRouter, Depends, Query, status

from core import *
from features.users.models import User

from .dependencies import active_support_user
from .guards import *
from .models import *
from .schemas import *
from .service import support_service

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/cases", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    data: SupportCaseCreate = Depends(valid_support_create),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
):
    return support_service.create_case(db, data, user)


@router.get("/cases", response_model=list[SupportCaseResponse])
def list_cases(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
):
    return support_service.list_cases(db, user, limit, offset)


@router.get("/cases/detail", response_model=SupportCaseResponse)
def get_case(case: SupportCase = Depends(accessible_support_case)):
    return case


@router.get("/messages", response_model=list[SupportMessageResponse])
def list_messages(
    case: SupportCase = Depends(accessible_support_case),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return support_service.list_messages(db, case, limit, offset)


@router.post(
    "/messages", response_model=SupportMessageResponse, status_code=status.HTTP_201_CREATED
)
def add_message(
    data: SupportMessageCreate,
    case: SupportCase = Depends(accessible_support_case),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
):
    return support_service.add_message(db, case, user, data)


@router.patch("/cases/status", response_model=SupportCaseResponse)
def update_status(
    data: SupportStatusUpdate,
    case: SupportCase = Depends(managed_support_case),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
):
    return support_service.update_status(db, case, data, user.id)


@router.post("/cases/assign", response_model=SupportCaseResponse)
def assign_case(
    case: SupportCase = Depends(managed_support_case),
    user: User = Depends(active_support_user),
    db: Session = Depends(get_db),
):
    return support_service.assign_to_self(db, case, user)
