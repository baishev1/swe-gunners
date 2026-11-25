from fastapi import APIRouter, Depends, Response, status

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
    return TokenResponse(
        access_token=auth_service.create_access_token(user),
        refresh_token=auth_service.create_refresh_token(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(user: User = Depends(valid_refresh_token)):
    return TokenResponse(
        access_token=auth_service.create_access_token(user),
        refresh_token=auth_service.create_refresh_token(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/verify-email", response_model=UserResponse)
def verify_email(user: User = Depends(valid_verify_token), db: Session = Depends(get_db)):
    return auth_service.verify_email(db=db, user=user)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
def resend_verification(user: User = Depends(get_current_user)):
    auth_service.send_verification_email(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db=db, email=data.email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    data: ResetPasswordRequest,
    user: User = Depends(valid_reset_token),
    db: Session = Depends(get_db),
):
    auth_service.reset_password(db=db, user=user, new_password=data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
