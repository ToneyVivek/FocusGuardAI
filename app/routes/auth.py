from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.dependencies.deps import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.models import User
from app.schemas.schemas import AdminRegisterRequest, OnboardingSetup, Token, UserResponse
from app.services.auth import authenticate_user, register_bootstrap_admin
from app.services.invitation import process_onboarding_setup

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, user_in: AdminRegisterRequest, db: Session = Depends(get_db)):
    """
    Bootstrap registration for the first platform administrator only.
    Employee accounts must onboard via invitation (POST /auth/complete-setup).
    """
    return register_bootstrap_admin(
        db=db,
        email=user_in.email,
        full_name=user_in.full_name,
        password=user_in.password,
    )


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2-compatible login returning a JWT access token."""
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.email,
        role=user.role,
        user_id=user.id,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieves the profile of the currently authenticated user."""
    return current_user


@router.post("/complete-setup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def complete_setup(request: Request, setup_in: OnboardingSetup, db: Session = Depends(get_db)):
    """Completes onboarding for an invited employee using a secure invitation token."""
    return process_onboarding_setup(db=db, setup_in=setup_in)
