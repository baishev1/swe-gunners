from fastapi import APIRouter, Depends, status

from core import *
from features.users.models import User

from .guards import *
from .schemas import *
from .service import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest = Depends(unique_email_guard), db: Session = Depends(get_db)):
    return auth_service.register(db=db, **data.model_dump())


@router.post("/login", response_model=TokenResponse)
def login(user: User = Depends(valid_credentials_guard)):
    return TokenResponse(access_token=auth_service.create_access_token(user))


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user
